package com.waterapproval.service;

import com.waterapproval.dto.ApplicationResponse;
import com.waterapproval.dto.CreateApplicationRequest;
import com.waterapproval.dto.ReviewResponse;
import com.waterapproval.entity.Application;
import com.waterapproval.exception.ApplicationNotFoundException;
import com.waterapproval.repository.ApplicationRepository;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
public class ApplicationService {

    private final ApplicationRepository repository;
    private final AiServiceClient aiServiceClient;

    public ApplicationService(ApplicationRepository repository, AiServiceClient aiServiceClient) {
        this.repository = repository;
        this.aiServiceClient = aiServiceClient;
        seedData();
    }

    public List<ApplicationResponse> listApplications() {
        return repository.findAll(Sort.by(Sort.Direction.DESC, "id")).stream()
                .map(this::toResponse)
                .toList();
    }

    public ApplicationResponse getApplication(Long id) {
        return toResponse(requireApplication(id));
    }

    @Transactional
    public ApplicationResponse createApplication(CreateApplicationRequest request, List<MultipartFile> files) {
        Application application = new Application();
        application.setApplicantName(request.getApplicantName());
        application.setApplicantId(request.getApplicantId());
        application.setProjectName(request.getProjectName());
        application.setWaterUse(request.getWaterUse());
        application.setLocation(request.getLocation());
        application.setApplicationDate(LocalDateTime.now());
        application.setStatus("PENDING");
        application.setFiles(saveFiles(files));
        application.setAttachments(new ArrayList<>(application.getFiles()));
        application = repository.save(application);
        return toResponse(application);
    }

    @Transactional
    public ReviewResponse reviewApplication(Long id) {
        Application application = requireApplication(id);
        Map<String, Object> payload = buildPayload(application);
        Map<String, Object> aiResponse = aiServiceClient.reviewApplication(payload);
        String status = (String) aiResponse.getOrDefault("status", "ERROR");
        application.setStatus(status);
        application.setReviewResult(JsonSupport.toJson(aiResponse));

        repository.save(application);

        ReviewResponse response = new ReviewResponse();
        response.setStatus(status);
        response.setMessage((String) aiResponse.getOrDefault("message", ""));
        return response;
    }

    @Transactional
    public ApplicationResponse updateApplication(Long id, CreateApplicationRequest request, List<MultipartFile> files) {
        Application application = requireApplication(id);

        application.setApplicantName(request.getApplicantName());
        application.setApplicantId(request.getApplicantId());
        application.setProjectName(request.getProjectName());
        application.setWaterUse(request.getWaterUse());
        application.setLocation(request.getLocation());
        application.setApplicationDate(LocalDateTime.now());

        if (files != null && !files.isEmpty()) {
            // 删除旧文件
            List<String> oldFiles = new ArrayList<>(application.getFiles());
            deleteStoredFiles(oldFiles);
            try {
                aiServiceClient.deleteKnowledge(oldFiles);
            } catch (Exception ex) {
                System.err.println("通知AI服务删除知识失败: " + ex.getMessage());
            }
            List<String> saved = saveFiles(files);
            application.setFiles(saved);
            application.setAttachments(new ArrayList<>(saved));
        }

        application = repository.save(application);
        return toResponse(application);
    }

    @Transactional
    public void deleteApplication(Long id) {
        Application application = requireApplication(id);
        // 删除存储的文件
        List<String> oldFiles = new ArrayList<>(application.getFiles());
        deleteStoredFiles(oldFiles);
        try {
            aiServiceClient.deleteKnowledge(oldFiles);
        } catch (Exception ex) {
            System.err.println("通知AI服务删除知识失败: " + ex.getMessage());
        }
        repository.delete(application);
    }

    private void deleteStoredFiles(List<String> fileNames) {
        if (fileNames == null || fileNames.isEmpty()) {
            return;
        }
        Path uploadDir = Paths.get("uploads");
        for (String fileName : fileNames) {
            try {
                Path target = uploadDir.resolve(fileName);
                Files.deleteIfExists(target);
            } catch (Exception ex) {
                // 记录异常但不阻止主流程
                System.err.println("无法删除文件: " + fileName + ", 错误: " + ex.getMessage());
            }
        }
    }

    private Application requireApplication(Long id) {
        return repository.findById(id).orElseThrow(() -> new ApplicationNotFoundException(id));
    }

    private ApplicationResponse toResponse(Application application) {
        ApplicationResponse response = new ApplicationResponse();
        response.setId(application.getId());
        response.setApplicantName(application.getApplicantName());
        response.setApplicantId(application.getApplicantId());
        response.setProjectName(application.getProjectName());
        response.setWaterUse(application.getWaterUse());
        response.setLocation(application.getLocation());
        response.setApplicationDate(application.getApplicationDate());
        response.setStatus(application.getStatus());
        response.setReviewResult(application.getReviewResult());
        response.setFiles(application.getFiles());
        response.setAttachments(application.getAttachments());
        return response;
    }

    private Map<String, Object> buildPayload(Application application) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("applicant_name", application.getApplicantName());
        payload.put("applicant_id", application.getApplicantId());
        payload.put("project_name", application.getProjectName());
        payload.put("water_use", application.getWaterUse());
        payload.put("location", application.getLocation());
        payload.put("attachments", application.getFiles());
        return payload;
    }

    private List<String> saveFiles(List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            return new ArrayList<>();
        }

        Path uploadDir = Paths.get("uploads");
        try {
            if (!Files.exists(uploadDir)) {
                Files.createDirectories(uploadDir);
            }
        } catch (IOException e) {
            throw new RuntimeException("无法创建上传目录", e);
        }

        List<String> savedFileNames = new ArrayList<>();
        for (MultipartFile file : files) {
            String originalFileName = file.getOriginalFilename();
            if (originalFileName == null || originalFileName.isBlank()) {
                continue;
            }

            // 为了防止文件名重复，在原文件名前加上 UUID
            String safeFileName = UUID.randomUUID().toString() + "_" + originalFileName;
            Path targetPath = uploadDir.resolve(safeFileName);

            try {
                Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);
                savedFileNames.add(safeFileName);
            } catch (IOException e) {
                throw new RuntimeException("文件保存失败: " + originalFileName, e);
            }
        }
        return savedFileNames;
    }

    private void seedData() {
        if (repository.count() > 0) {
            return;
        }

        Application first = new Application();
        first.setApplicantName("张三");
        first.setApplicantId("330101199001011234");
        first.setProjectName("城市供水项目");
        first.setWaterUse("生活用水");
        first.setLocation("浙江省杭州市");
        first.setApplicationDate(LocalDateTime.now().minusDays(1));
        first.setStatus("PENDING");
        first.setFiles(List.of("水资源论证报告.pdf", "营业执照复印件.pdf"));
        first.setAttachments(List.of("水资源论证报告.pdf", "营业执照复印件.pdf"));
        repository.save(first);

        Application second = new Application();
        second.setApplicantName("李四");
        second.setApplicantId("330101199202021234");
        second.setProjectName("农业灌溉项目");
        second.setWaterUse("农业用水");
        second.setLocation("浙江省宁波市");
        second.setApplicationDate(LocalDateTime.now().minusHours(6));
        second.setStatus("APPROVED");
        second.setFiles(List.of("申请表.pdf", "承诺书.pdf"));
        second.setAttachments(List.of("申请表.pdf", "承诺书.pdf"));
        second.setReviewResult(
                "{\"status\":\"APPROVED\",\"message\":\"示例审核结果\",\"details\":{\"completeness\":{\"complete\":true},\"knowledge_hits\":[]}} ");
        repository.save(second);
    }

    private static final class JsonSupport {
        private static final com.fasterxml.jackson.databind.ObjectMapper MAPPER = new com.fasterxml.jackson.databind.ObjectMapper();

        private JsonSupport() {
        }

        private static String toJson(Object value) {
            try {
                return MAPPER.writeValueAsString(value);
            } catch (Exception ex) {
                return "{}";
            }
        }
    }
}
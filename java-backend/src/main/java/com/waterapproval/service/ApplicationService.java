package com.waterapproval.service;

import com.waterapproval.dto.ApplicationResponse;
import com.waterapproval.dto.CreateApplicationRequest;
import com.waterapproval.dto.ReviewResponse;
import com.waterapproval.entity.Application;
import com.waterapproval.exception.ApplicationNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Service
public class ApplicationService {

    private final Map<Long, Application> store = new ConcurrentHashMap<>();
    private final AtomicLong sequence = new AtomicLong(1);
    private final AiServiceClient aiServiceClient;

    public ApplicationService(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
        seedData();
    }

    public List<ApplicationResponse> listApplications() {
        return store.values().stream()
                .sorted((left, right) -> right.getId().compareTo(left.getId()))
                .map(this::toResponse)
                .toList();
    }

    public ApplicationResponse getApplication(Long id) {
        return toResponse(requireApplication(id));
    }

    public ApplicationResponse createApplication(CreateApplicationRequest request, List<MultipartFile> files) {
        Application application = new Application();
        application.setId(sequence.getAndIncrement());
        application.setApplicantName(request.getApplicantName());
        application.setApplicantId(request.getApplicantId());
        application.setProjectName(request.getProjectName());
        application.setWaterUse(request.getWaterUse());
        application.setLocation(request.getLocation());
        application.setApplicationDate(LocalDateTime.now());
        application.setStatus("PENDING");
        application.setFiles(extractFileNames(files));
        store.put(application.getId(), application);
        return toResponse(application);
    }

    public ReviewResponse reviewApplication(Long id) {
        Application application = requireApplication(id);
        Map<String, Object> payload = buildPayload(application);
        Map<String, Object> aiResponse = aiServiceClient.reviewApplication(payload);
        String status = (String) aiResponse.getOrDefault("status", "ERROR");
        application.setStatus(status);
        application.setReviewResult(JsonSupport.toJson(aiResponse));
        
        ReviewResponse response = new ReviewResponse();
        response.setStatus(status);
        response.setMessage((String) aiResponse.getOrDefault("message", ""));
        return response;
    }

    private Application requireApplication(Long id) {
        Application application = store.get(id);
        if (application == null) {
            throw new ApplicationNotFoundException(id);
        }
        return application;
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

    private List<String> extractFileNames(List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            return new ArrayList<>();
        }
        return files.stream()
                .map(MultipartFile::getOriginalFilename)
                .filter(name -> name != null && !name.isBlank())
                .toList();
    }

    private void seedData() {
        Application first = new Application();
        first.setId(sequence.getAndIncrement());
        first.setApplicantName("张三");
        first.setApplicantId("330101199001011234");
        first.setProjectName("城市供水项目");
        first.setWaterUse("生活用水");
        first.setLocation("浙江省杭州市");
        first.setApplicationDate(LocalDateTime.now().minusDays(1));
        first.setStatus("PENDING");
        first.setFiles(List.of("水资源论证报告.pdf", "营业执照复印件.pdf"));
        first.setAttachments(List.of("水资源论证报告.pdf", "营业执照复印件.pdf"));
        store.put(first.getId(), first);

        Application second = new Application();
        second.setId(sequence.getAndIncrement());
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
        store.put(second.getId(), second);
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
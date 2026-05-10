package com.waterapproval.controller;

import com.waterapproval.dto.ApplicationResponse;
import com.waterapproval.dto.CreateApplicationRequest;
import com.waterapproval.dto.ReviewResponse;
import com.waterapproval.service.ApplicationService;
import com.waterapproval.service.AiServiceClient;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/applications")
public class ApplicationController {

    private final ApplicationService applicationService;
    private final AiServiceClient aiServiceClient;

    public ApplicationController(
            ApplicationService applicationService,
            AiServiceClient aiServiceClient) {
        this.applicationService = applicationService;
        this.aiServiceClient = aiServiceClient;
    }

    @GetMapping
    public List<ApplicationResponse> listApplications() {
        return applicationService.listApplications();
    }

    @GetMapping("/{id}")
    public ApplicationResponse getApplication(@PathVariable Long id) {
        return applicationService.getApplication(id);
    }

    @PostMapping
    public ResponseEntity<ApplicationResponse> createApplication(
            @Valid @ModelAttribute CreateApplicationRequest request,
            @RequestParam(value = "files", required = false) List<MultipartFile> files) {
        ApplicationResponse created = applicationService.createApplication(request, files);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PostMapping("/{id}/review")
    public ReviewResponse reviewApplication(@PathVariable Long id) {
        return applicationService.reviewApplication(id);
    }

    @PostMapping("/{id}/ai-review")
    public Map<String, Object> aiReviewApplication(@PathVariable Long id) {
        ApplicationResponse app = applicationService.getApplication(id);
        Map<String, Object> appData = Map.of(
                "applicant_name", app.getApplicantName(),
                "applicant_id", app.getApplicantId(),
                "project_name", app.getProjectName(),
                "water_use", app.getWaterUse(),
                "location", app.getLocation(),
                "attachments", app.getAttachments()
        );
        return aiServiceClient.reviewApplication(appData);
    }
}

@RestController
@RequestMapping("/api/ai")
class AiController {

    private final AiServiceClient aiServiceClient;

    public AiController(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    @GetMapping("/tools")
    public Map<String, Object> getTools() {
        return aiServiceClient.getMcpTools();
    }

    @GetMapping("/knowledge/search")
    public Map<String, Object> searchKnowledge(
            @RequestParam String q,
            @RequestParam(required = false, defaultValue = "4") Integer topK) {
        return aiServiceClient.searchKnowledge(q, topK);
    }

    @PostMapping("/review")
    public Map<String, Object> review(@RequestBody Map<String, Object> application) {
        return aiServiceClient.reviewApplication(application);
    }

    @PostMapping("/check-completeness")
    public Map<String, Object> checkCompleteness(@RequestBody Map<String, Object> application) {
        return aiServiceClient.checkCompleteness(application);
    }
}

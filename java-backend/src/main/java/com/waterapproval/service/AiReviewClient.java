package com.waterapproval.service;

import com.waterapproval.dto.ReviewResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
public class AiReviewClient {

    private final RestTemplate restTemplate;
    private final String baseUrl;

    public AiReviewClient(RestTemplate restTemplate, @Value("${app.ai-service-base-url}") String baseUrl) {
        this.restTemplate = restTemplate;
        this.baseUrl = baseUrl;
    }

    public ReviewResponse review(Map<String, Object> applicationPayload) {
        try {
            Map<String, Object> request = Map.of("application", applicationPayload);
            ReviewResponse response = restTemplate.postForObject(baseUrl + "/api/review", request,
                    ReviewResponse.class);
            if (response != null) {
                return response;
            }
        } catch (Exception ex) {
            return createFallbackResponse(ex.getMessage());
        }

        return createFallbackResponse("AI service returned an empty response");
    }

    private ReviewResponse createFallbackResponse(String errorMessage) {
        ReviewResponse fallback = new ReviewResponse();
        fallback.setStatus("PENDING");
        fallback.setMessage("AI service unavailable, fallback to manual review");
        fallback.setDetails(Map.of("error", errorMessage));
        return fallback;
    }
}
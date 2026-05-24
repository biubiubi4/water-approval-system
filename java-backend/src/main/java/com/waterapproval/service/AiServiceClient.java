package com.waterapproval.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiServiceClient {

    private final RestTemplate restTemplate;
    private final String aiServiceUrl;

    public AiServiceClient(
            RestTemplate restTemplate,
            @Value("${app.ai-service-base-url:http://localhost:8000}") String aiServiceUrl
    ) {
        this.restTemplate = restTemplate;
        this.aiServiceUrl = aiServiceUrl;
    }

    public Map<String, Object> reviewApplication(Map<String, Object> applicationData) {
        String url = aiServiceUrl + "/api/review";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("application", applicationData);
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("status", "ERROR");
            errorResult.put("message", "AI服务不可用: " + e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> checkCompleteness(Map<String, Object> applicationData) {
        String url = aiServiceUrl + "/api/check-completeness";
        
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("application", applicationData);
        
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> searchKnowledge(String query, Integer topK) {
        String url = aiServiceUrl + "/api/knowledge/search?q=" + query + "&top_k=" + (topK != null ? topK : 4);
        
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> getMcpTools() {
        String url = aiServiceUrl + "/api/mcp/tools";
        
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> getKnowledgeStats() {
        String url = aiServiceUrl + "/api/knowledge/stats";

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> listKnowledgeRecords(String query, String source, String recordType) {
        UriComponentsBuilder builder = UriComponentsBuilder.fromHttpUrl(aiServiceUrl + "/api/knowledge/records");
        if (query != null && !query.isBlank()) {
            builder.queryParam("q", query);
        }
        if (source != null && !source.isBlank()) {
            builder.queryParam("source", source);
        }
        if (recordType != null && !recordType.isBlank()) {
            builder.queryParam("record_type", recordType);
        }

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(builder.toUriString(), Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> getKnowledgeRecord(String recordId) {
        String url = aiServiceUrl + "/api/knowledge/records/" + recordId;

        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> createKnowledgeRecord(Map<String, Object> payload) {
        String url = aiServiceUrl + "/api/knowledge/records";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> updateKnowledgeRecord(String recordId, Map<String, Object> payload) {
        String url = aiServiceUrl + "/api/knowledge/records/" + recordId;

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(payload, headers);

        try {
            ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.PUT, request, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> deleteKnowledgeRecord(String recordId) {
        String url = aiServiceUrl + "/api/knowledge/records/" + recordId;

        try {
            ResponseEntity<Map> response = restTemplate.exchange(url, HttpMethod.DELETE, HttpEntity.EMPTY, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }

    public Map<String, Object> deleteKnowledge(java.util.List<String> fileNames) {
        String url = aiServiceUrl + "/api/knowledge/delete";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> body = new HashMap<>();
        body.put("files", fileNames);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
            return response.getBody();
        } catch (Exception e) {
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("error", e.getMessage());
            return errorResult;
        }
    }
}

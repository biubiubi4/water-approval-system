package com.waterapproval.controller;

import com.waterapproval.service.AiServiceClient;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    private final AiServiceClient aiServiceClient;

    public KnowledgeController(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    @GetMapping("/stats")
    public Map<String, Object> getKnowledgeStats() {
        return aiServiceClient.getKnowledgeStats();
    }

    @GetMapping("/records")
    public Map<String, Object> listKnowledgeRecords(
            @RequestParam(value = "q", required = false) String query,
            @RequestParam(value = "source", required = false) String source,
            @RequestParam(value = "record_type", required = false) String recordType) {
        return aiServiceClient.listKnowledgeRecords(query, source, recordType);
    }

    @GetMapping("/records/{recordId}")
    public Map<String, Object> getKnowledgeRecord(@PathVariable String recordId) {
        return aiServiceClient.getKnowledgeRecord(recordId);
    }

    @PostMapping("/records")
    public Map<String, Object> createKnowledgeRecord(@RequestBody Map<String, Object> payload) {
        return aiServiceClient.createKnowledgeRecord(payload);
    }

    @PutMapping("/records/{recordId}")
    public Map<String, Object> updateKnowledgeRecord(
            @PathVariable String recordId,
            @RequestBody Map<String, Object> payload) {
        return aiServiceClient.updateKnowledgeRecord(recordId, payload);
    }

    @DeleteMapping("/records/{recordId}")
    public Map<String, Object> deleteKnowledgeRecord(@PathVariable String recordId) {
        return aiServiceClient.deleteKnowledgeRecord(recordId);
    }
}

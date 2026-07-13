package com.waterapproval.controller;

import com.waterapproval.service.AiServiceClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    private final AiServiceClient aiServiceClient;

    public KnowledgeController(AiServiceClient aiServiceClient) {
        this.aiServiceClient = aiServiceClient;
    }

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Map<String, Object> uploadKnowledgeFiles(
            @RequestParam(value = "files", required = false) List<MultipartFile> files) {
        return aiServiceClient.uploadKnowledgeFiles(files);
    }

    @GetMapping("/search")
    public Map<String, Object> searchKnowledge(
            @RequestParam String q,
            @RequestParam(value = "top_k", required = false, defaultValue = "4") Integer topK) {
        return aiServiceClient.searchKnowledge(q, topK);
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

    @PostMapping("/records/batch-delete")
    public Map<String, Object> batchDeleteKnowledgeRecords(@RequestBody Map<String, List<String>> payload) {
        return aiServiceClient.batchDeleteKnowledgeRecords(payload.getOrDefault("ids", List.of()));
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

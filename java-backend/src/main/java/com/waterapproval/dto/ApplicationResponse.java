package com.waterapproval.dto;

import java.time.LocalDateTime;
import java.util.List;

public class ApplicationResponse {

    private Long id;
    private String applicantName;
    private String applicantId;
    private String projectName;
    private String waterUse;
    private String location;
    private LocalDateTime applicationDate;
    private String status;
    private String reviewResult;
    private java.util.List<Object> reviewHistory;
    private List<String> files;
    private List<String> attachments;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getApplicantName() {
        return applicantName;
    }

    public void setApplicantName(String applicantName) {
        this.applicantName = applicantName;
    }

    public String getApplicantId() {
        return applicantId;
    }

    public void setApplicantId(String applicantId) {
        this.applicantId = applicantId;
    }

    public String getProjectName() {
        return projectName;
    }

    public void setProjectName(String projectName) {
        this.projectName = projectName;
    }

    public String getWaterUse() {
        return waterUse;
    }

    public void setWaterUse(String waterUse) {
        this.waterUse = waterUse;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public LocalDateTime getApplicationDate() {
        return applicationDate;
    }

    public void setApplicationDate(LocalDateTime applicationDate) {
        this.applicationDate = applicationDate;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getReviewResult() {
        return reviewResult;
    }

    public void setReviewResult(String reviewResult) {
        this.reviewResult = reviewResult;
    }

    public java.util.List<Object> getReviewHistory() {
        return reviewHistory;
    }

    public void setReviewHistory(java.util.List<Object> reviewHistory) {
        this.reviewHistory = reviewHistory;
    }

    public List<String> getFiles() {
        return files;
    }

    public void setFiles(List<String> files) {
        this.files = files;
    }

    public List<String> getAttachments() {
        return attachments;
    }

    public void setAttachments(List<String> attachments) {
        this.attachments = attachments;
    }
}
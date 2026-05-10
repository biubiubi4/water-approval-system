package com.waterapproval.dto;

import jakarta.validation.constraints.NotBlank;

public class CreateApplicationRequest {

    @NotBlank
    private String applicantName;

    @NotBlank
    private String applicantId;

    private String projectName;
    private String waterUse;
    private String location;

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
}
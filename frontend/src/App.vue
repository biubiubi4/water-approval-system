<template>
  <div class="app-container">
    <header class="header">
      <h1>涉水审批智能审核系统</h1>
      <nav class="nav">
        <button @click="currentPage = 'list'" :class="{ active: currentPage === 'list' }">申请列表</button>
        <button @click="newApplication" :class="{ active: currentPage === 'create' }">新建申请</button>
        <button @click="currentPage = 'knowledge'" :class="{ active: currentPage === 'knowledge' }">知识库管理</button>
      </nav>
    </header>

    <main class="main-content">
      <ApplicationList v-if="currentPage === 'list'" @select-application="viewDetails" @edit-application="editApplication" @review-application="viewResult" />
      <CreateApplication v-if="currentPage === 'create'" :application="selectedApplication" @saved="onSaved" />
      <ReviewResult v-if="currentPage === 'result'" :application="selectedApplication" />
      <ApplicationDetails v-if="currentPage === 'details'" :application="selectedApplication" />
      <KnowledgeManager v-if="currentPage === 'knowledge'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ApplicationList from './components/ApplicationList.vue'
import CreateApplication from './components/CreateApplication.vue'
import ReviewResult from './components/ReviewResult.vue'
import ApplicationDetails from './components/ApplicationDetails.vue'
import KnowledgeManager from './components/KnowledgeManager.vue'

const currentPage = ref('list')
const selectedApplication = ref(null)

const viewResult = (application) => {
  selectedApplication.value = application
  currentPage.value = 'result'
}

const viewDetails = (application) => {
  selectedApplication.value = application
  currentPage.value = 'details'
}

const editApplication = (application) => {
  selectedApplication.value = application
  currentPage.value = 'create'
}

const onSaved = () => {
  selectedApplication.value = null
  currentPage.value = 'list'
}

const newApplication = () => {
  selectedApplication.value = null
  currentPage.value = 'create'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  font-family: Arial, Helvetica, sans-serif;
  background: #f6f7f9;
  color: #1f2937;
}

.app-container {
  min-height: 100vh;
  background: #f6f7f9;
}

.header {
  background: #ffffff;
  color: #111827;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.header h1 {
  font-size: 1.35rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.nav {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.nav button {
  padding: 0.45rem 0.85rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.nav button:hover,
.nav button.active {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.main-content {
  padding: 1.25rem;
}
</style>

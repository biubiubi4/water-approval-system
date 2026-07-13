<template>
  <div class="app-container">
    <header class="header">
      <div class="header-inner">
        <div>
          <h1>涉水审批智能审核系统</h1>
          <p>取水许可材料预审、法规检索与 AI 复核工作台</p>
        </div>
        <nav class="nav">
          <button @click="currentPage = 'list'" :class="{ active: currentPage === 'list' }">申请列表</button>
          <button @click="newApplication" :class="{ active: currentPage === 'create' }">新建申请</button>
          <button @click="currentPage = 'knowledge'" :class="{ active: currentPage === 'knowledge' }">知识库管理</button>
        </nav>
      </div>
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
  background: #eef2f7;
  color: #1f2937;
}

.app-container {
  min-height: 100vh;
  background:
    linear-gradient(180deg, #eaf2ff 0, rgba(234, 242, 255, 0) 280px),
    #f5f7fb;
}

.header {
  background: #ffffff;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
}

.header-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 1.1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.header h1 {
  font-size: 1.4rem;
  margin-bottom: 0.25rem;
  font-weight: 700;
  color: #0f172a;
}

.header p {
  color: #64748b;
  font-size: 0.92rem;
}

.nav {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nav button {
  padding: 0.58rem 0.9rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #ffffff;
  color: #374151;
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s;
}

.nav button:hover,
.nav button.active {
  background: #eff6ff;
  border-color: #93c5fd;
  color: #1d4ed8;
}

.main-content {
  max-width: 1180px;
  margin: 0 auto;
  padding: 1.5rem;
}

@media (max-width: 760px) {
  .header-inner {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>

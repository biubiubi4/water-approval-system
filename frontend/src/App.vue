<template>
  <div class="app-container">
    <header class="header">
      <h1>涉水审批智能审核系统</h1>
      <nav class="nav">
        <button @click="currentPage = 'list'" :class="{ active: currentPage === 'list' }">申请列表</button>
        <button @click="newApplication" :class="{ active: currentPage === 'create' }">新建申请</button>
        <button @click="currentPage = 'result'" :class="{ active: currentPage === 'result' }">初审结果</button>
        <button @click="currentPage = 'knowledge'" :class="{ active: currentPage === 'knowledge' }">知识库管理</button>
      </nav>
    </header>
    <main class="main-content">
      <ApplicationList v-if="currentPage === 'list'" @select-application="viewDetails" @edit-application="editApplication" />
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
  // 清除选中并跳回列表
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

.app-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  background-color: #1e40af;
  color: white;
  padding: 1rem 2rem;
}

.header h1 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.nav {
  display: flex;
  gap: 1rem;
}

.nav button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: rgba(255, 255, 255, 0.2);
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}

.nav button:hover,
.nav button.active {
  background-color: rgba(255, 255, 255, 0.3);
}

.main-content {
  padding: 2rem;
}
</style>
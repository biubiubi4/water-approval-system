<template>
  <div class="application-details">
    <h2>申请详情</h2>
    <div v-if="application" class="details">
      <div class="row"><strong>申请ID:</strong> {{ application.id }}</div>
      <div class="row"><strong>申请人姓名:</strong> {{ application.applicantName }}</div>
      <div class="row"><strong>证件号码:</strong> {{ maskId(application.applicantId) }}</div>
      <div class="row"><strong>项目名称:</strong> {{ application.projectName }}</div>
      <div class="row"><strong>用水类型:</strong> {{ application.waterUse }}</div>
      <div class="row"><strong>位置:</strong> {{ application.location }}</div>
      <div class="row"><strong>申请日期:</strong> {{ formatDate(application.applicationDate) }}</div>

      <div class="attachments" v-if="application.files && application.files.length">
        <h3>附件</h3>
        <ul>
          <li v-for="(f, idx) in application.files" :key="idx">{{ f }}</li>
        </ul>
      </div>
    </div>
    <div v-else class="no-selection">
      <p>未选择申请。</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  application: { type: Object, default: null }
})

const maskId = (id) => {
  if (!id) return ''
  return id.slice(0, 3) + '****' + id.slice(-4)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.application-details { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); max-width: 800px; margin: 0 auto; }
.application-details h2 { color: #1e40af; margin-bottom: 1rem }
.row { margin-bottom: 0.5rem }
.attachments h3 { margin-top: 1rem }
</style>

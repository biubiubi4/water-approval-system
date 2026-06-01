<template>
  <div class="review-result">
    <h2>初审结果</h2>
    <div v-if="application" class="result-content">
      <div class="application-info">
        <h3>申请信息</h3>
        <div class="info-row">
          <span class="label">申请ID</span>
          <span class="value">{{ application.id }}</span>
        </div>
        <div class="info-row">
          <span class="label">申请人姓名</span>
          <span class="value">{{ application.applicantName }}</span>
        </div>
        <div class="info-row">
          <span class="label">证件号码</span>
          <span class="value">{{ maskId(application.applicantId) }}</span>
        </div>
        <div class="info-row">
          <span class="label">申请日期</span>
          <span class="value">{{ formatDate(application.applicationDate) }}</span>
        </div>
        <div class="info-row">
          <span class="label">审核状态</span>
          <span :class="getStatusClass(application.status)" class="status-value">{{ getStatusText(application.status) }}</span>
        </div>
      </div>
      
      <div class="review-details">
        <h3>审核详情</h3>
        <div v-if="reviewResult" class="result-details">
          <div class="result-summary">
            <div :class="resultIconClass" class="result-icon">
              <span v-if="isApproved">✓</span>
              <span v-else-if="isRejected">✗</span>
              <span v-else>?</span>
            </div>
            <div class="result-message">
              <p class="result-title">{{ reviewResult.message }}</p>
            </div>
          </div>
          
          <div v-if="reviewResult.details" class="details-section">
            <div class="detail-item">
              <span class="detail-label">材料完整性</span>
              <span class="detail-value">{{ reviewResult.details.completeness }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">合规性判断</span>
              <span class="detail-value">{{ reviewResult.details.compliance }}</span>
            </div>
            
            <div v-if="reviewResult.details.suggestions && reviewResult.details.suggestions.length > 0" class="suggestions">
              <h4>修改建议与不合规清单</h4>
              <textarea 
                readonly 
                class="suggestions-textbox"
                rows="6"
                :value="Array.isArray(reviewResult.details.suggestions) ? reviewResult.details.suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n') : reviewResult.details.suggestions"
                style="width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 4px; background: #f9fafb; color: #374151; font-family: inherit; font-size: 0.9rem; resize: vertical;"
              ></textarea>
            </div>
          </div>
        </div>
        
        <div v-else class="no-result">
          <p>暂无审核结果</p>
        </div>

        <div class="review-actions" style="margin-top: 1.5rem; text-align: center;">
          <button @click="triggerReview" :disabled="isReviewing" class="btn-review">
            <span v-if="isReviewing">审核中...</span>
            <span v-else>{{ reviewResult ? '重新审核' : '开始审核' }}</span>
          </button>
        </div>

        <div v-if="application.reviewResult" class="raw-response" style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid #eee;">
          <h4>原始返回内容</h4>
          <pre class="raw-content" style="background: #f3f4f6; padding: 1rem; border-radius: 4px; overflow-x: auto; font-size: 0.875rem; color: #374151; white-space: pre-wrap;">{{ typeof application.reviewResult === 'object' ? JSON.stringify(application.reviewResult, null, 2) : (function(){ try { return JSON.stringify(JSON.parse(application.reviewResult), null, 2) } catch(e) { return application.reviewResult } })() }}</pre>
        </div>
      </div>
    </div>
    
    <div v-else class="no-application">
      <p>请选择一个申请查看审核结果</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  application: {
    type: Object,
    default: null
  }
})

const reviewResult = ref(null)
const isReviewing = ref(false)

const maskId = (id) => {
  if (!id) return ''
  return id.slice(0, 3) + '****' + id.slice(-4)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatSimilarity = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

const formatScore = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

const getStatusClass = (status) => {
  const classes = {
    'PENDING': 'status-pending',
    'APPROVED': 'status-approved',
    'REJECTED': 'status-rejected',
    'ERROR': 'status-error'
  }
  return classes[status] || 'status-unknown'
}

const getStatusText = (status) => {
  const texts = {
    'PENDING': '待审核',
    'APPROVED': '审核通过',
    'REJECTED': '审核未通过',
    'ERROR': '审核异常'
  }
  return texts[status] || status
}

const isApproved = computed(() => {
  return props.application?.status === 'APPROVED'
})

const isRejected = computed(() => {
  return props.application?.status === 'REJECTED'
})

const resultIconClass = computed(() => {
  if (isApproved.value) return 'icon-approved'
  if (isRejected.value) return 'icon-rejected'
  return 'icon-pending'
})

const parseReviewResult = () => {
  if (props.application?.reviewResult) {
    try {
      reviewResult.value = JSON.parse(props.application.reviewResult)
    } catch (e) {
      reviewResult.value = {
        message: props.application.reviewResult,
        details: {}
      }
    }
  } else {
    reviewResult.value = null
  }
}

const triggerReview = async () => {
  if (!props.application?.id) return
  
  isReviewing.value = true
  try {
    await axios.post(`/api/applications/${props.application.id}/review`)
    // 刷新申请信息
    const response = await axios.get(`/api/applications/${props.application.id}`)
    props.application.status = response.data.status
    props.application.reviewResult = response.data.reviewResult
    parseReviewResult()
  } catch (error) {
    console.error('审核失败:', error)
  } finally {
    isReviewing.value = false
  }
}

watch(() => props.application, () => {
  parseReviewResult()
}, { immediate: true })
</script>

<style scoped>
.review-result {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 800px;
  margin: 0 auto;
}

.review-result h2 {
  margin-bottom: 1.5rem;
  color: #1e40af;
}

.application-info {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #eee;
}

.application-info h3 {
  margin-bottom: 1rem;
  color: #374151;
}

.info-row {
  display: flex;
  margin-bottom: 0.75rem;
}

.info-row .label {
  width: 120px;
  font-weight: 600;
  color: #6b7280;
}

.info-row .value {
  flex: 1;
}

.status-value {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status-pending {
  background-color: #fef3c7;
  color: #d97706;
}

.status-approved {
  background-color: #dcfce7;
  color: #16a34a;
}

.status-rejected {
  background-color: #fee2e2;
  color: #dc2626;
}

.status-error {
  background-color: #e0e7ff;
  color: #4338ca;
}

.review-details h3 {
  margin-bottom: 1rem;
  color: #374151;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 8px;
}

.result-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.icon-approved {
  background-color: #dcfce7;
  color: #16a34a;
}

.icon-rejected {
  background-color: #fee2e2;
  color: #dc2626;
}

.icon-pending {
  background-color: #fef3c7;
  color: #d97706;
}

.result-message .result-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.details-section {
  margin-top: 1rem;
}

.detail-item {
  display: flex;
  margin-bottom: 0.75rem;
}

.detail-item .detail-label {
  width: 120px;
  font-weight: 600;
  color: #6b7280;
}

.detail-item .detail-value {
  flex: 1;
}

.suggestions {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #fef3c7;
  border-radius: 8px;
}

.suggestions h4 {
  margin-bottom: 0.5rem;
  color: #d97706;
}

.suggestions ul {
  margin: 0;
  padding-left: 1.5rem;
}

.suggestions li {
  margin-bottom: 0.25rem;
  color: #78350f;
}

.knowledge-hits {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.knowledge-hits h4 {
  margin-bottom: 0.75rem;
  color: #374151;
}

.hit-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.9rem 1rem;
  margin-bottom: 0.8rem;
  background: #f9fafb;
}

.hit-card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: center;
  margin-bottom: 0.55rem;
}

.hit-score {
  padding: 0.2rem 0.5rem;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 0.85rem;
  white-space: nowrap;
}

.hit-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: #6b7280;
  margin-bottom: 0.55rem;
}

.hit-content {
  line-height: 1.7;
  color: #111827;
}

.no-result,
.no-application {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

.btn-review {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #1e40af;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-review:hover:not(:disabled) {
  background-color: #1e3a8a;
}

.btn-review:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
</style>
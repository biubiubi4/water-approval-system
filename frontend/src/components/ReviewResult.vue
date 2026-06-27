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
              <span class="detail-value">{{ formatCompleteness(reviewResult.details.completeness) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">合规性判断</span>
              <span class="detail-value">{{ formatCompliance(reviewResult.details.compliance) }}</span>
            </div>

            <div v-if="reviewResult.details.suggestions && reviewResult.details.suggestions.length > 0" class="suggestions">
              <h4>修改建议与不合规清单</h4>
              <textarea
                readonly
                class="suggestions-textbox"
                rows="6"
                :value="Array.isArray(reviewResult.details.suggestions) ? reviewResult.details.suggestions.map((s, i) => `${i + 1}. ${s}`).join('\n') : reviewResult.details.suggestions"
              ></textarea>
            </div>
          </div>
        </div>

        <div v-else class="no-result">
          <p>暂无审核结果</p>
        </div>

        <div class="review-actions">
          <button @click="triggerReview" :disabled="isReviewing" class="btn-review">
            <span v-if="isReviewing">审核中...</span>
            <span v-else>{{ reviewResult ? '重新审核' : '开始审核' }}</span>
          </button>
        </div>

        <div v-if="reviewSuggestions.length > 0" class="suggestions-section">
          <h4>修改建议</h4>
          <textarea
            readonly
            class="suggestions-textarea"
            rows="8"
            :value="reviewSuggestions.map((s, i) => `${i + 1}. ${s}`).join('\n')"
          ></textarea>
        </div>

        <div v-if="application.reviewResult" class="raw-response">
          <h4>原始返回内容</h4>
          <pre class="raw-content">{{ rawReviewText }}</pre>
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

const formatDetailValue = (value) => {
  if (value === null || value === undefined || value === '') return '暂无'
  if (typeof value === 'string') return value
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) return value.length ? value.join('；') : '暂无'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

const formatCompleteness = (value) => {
  if (!value || typeof value !== 'object') return formatDetailValue(value)
  const completeText = value.complete === true || value.status === 'PASS' ? '完整' : value.complete === false || value.status === 'FAIL' ? '不完整' : '未知'
  const missingItems = Array.isArray(value.missing_items) && value.missing_items.length ? `缺少材料：${value.missing_items.join('、')}` : ''
  const missingFields = Array.isArray(value.missing_fields) && value.missing_fields.length ? `缺少字段：${value.missing_fields.join('、')}` : ''
  const issues = Array.isArray(value.issues) && value.issues.length ? value.issues.join('；') : ''
  return [completeText, missingItems, missingFields, issues].filter(Boolean).join('；')
}

const formatCompliance = (value) => {
  if (!value || typeof value !== 'object') return formatDetailValue(value)
  const passText = value.pass === true || value.status === 'PASS' ? '通过' : value.pass === false || value.status === 'FAIL' ? '不通过' : '未知'
  const violations = Array.isArray(value.violations) && value.violations.length ? value.violations.join('；') : ''
  return [passText, violations].filter(Boolean).join('；')
}

const getStatusClass = (status) => {
  const classes = {
    PENDING: 'status-pending',
    APPROVED: 'status-approved',
    REJECTED: 'status-rejected',
    ERROR: 'status-error'
  }
  return classes[status] || 'status-unknown'
}

const getStatusText = (status) => {
  const texts = {
    PENDING: '待审核',
    APPROVED: '审核通过',
    REJECTED: '审核未通过',
    ERROR: '审核异常'
  }
  return texts[status] || status || '-'
}

const isApproved = computed(() => props.application?.status === 'APPROVED')
const isRejected = computed(() => props.application?.status === 'REJECTED')
const resultIconClass = computed(() => {
  if (isApproved.value) return 'icon-approved'
  if (isRejected.value) return 'icon-rejected'
  return 'icon-pending'
})

const rawReviewText = computed(() => {
  const value = props.application?.reviewResult
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  if (!value) return ''
  try {
    return JSON.stringify(JSON.parse(value), null, 2)
  } catch (error) {
    return String(value)
  }
})

const reviewSuggestions = computed(() => {
  if (!reviewResult.value) return []
  // 优先从 reviewResult 根级别获取 suggestions
  if (Array.isArray(reviewResult.value.suggestions)) {
    return reviewResult.value.suggestions
  }
  // 如果根级别没有，从 details 中获取
  if (reviewResult.value.details && Array.isArray(reviewResult.value.details.suggestions)) {
    return reviewResult.value.details.suggestions
  }
  return []
})

const parseReviewResult = () => {
  if (props.application?.reviewResult) {
    try {
      reviewResult.value = JSON.parse(props.application.reviewResult)
    } catch (error) {
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1.25rem;
  max-width: 800px;
  margin: 0 auto;
}

.review-result h2 {
  margin-bottom: 1.5rem;
  color: #111827;
  font-size: 1.15rem;
}

.application-info {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.application-info h3,
.review-details h3 {
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

.status-pending,
.status-approved,
.status-rejected,
.status-error {
  background-color: #f3f4f6;
  color: #4b5563;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 6px;
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
  background-color: #f3f4f6;
  color: #4b5563;
}

.result-message .result-title {
  font-size: 1.05rem;
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
  background-color: #f9fafb;
  border-radius: 6px;
}

.suggestions h4,
.raw-response h4 {
  margin-bottom: 0.5rem;
  color: #374151;
}

.suggestions-textbox,
.suggestions-textarea,
.raw-content {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: #ffffff;
  color: #374151;
  font-family: inherit;
  font-size: 0.9rem;
  resize: vertical;
  white-space: pre-wrap;
}

.suggestions-section {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #fffbeb;
  border: 1px solid #fef3c7;
  border-radius: 6px;
}

.suggestions-section h4 {
  margin-bottom: 0.75rem;
  color: #92400e;
  font-weight: 600;
}

.review-actions {
  margin-top: 1.5rem;
  text-align: center;
}

.btn-review {
  padding: 0.65rem 1rem;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;
  border-radius: 4px;
  cursor: pointer;
}

.btn-review:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.no-result,
.no-application {
  color: #6b7280;
  padding: 0.75rem 0;
}
</style>

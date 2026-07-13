<template>
  <div class="application-details">
    <h2>申请详情</h2>
    <div v-if="application" class="details">
      <section class="section-card">
        <h3>申请信息</h3>
        <div class="row"><strong>申请ID:</strong> {{ application.id }}</div>
        <div class="row"><strong>申请人姓名:</strong> {{ application.applicantName }}</div>
        <div class="row"><strong>证件号码:</strong> {{ maskId(application.applicantId) }}</div>
        <div class="row"><strong>项目名称:</strong> {{ application.projectName || '-' }}</div>
        <div class="row"><strong>用水类型:</strong> {{ application.waterUse || '-' }}</div>
        <div class="row"><strong>位置:</strong> {{ application.location || '-' }}</div>
        <div class="row"><strong>申请日期:</strong> {{ formatDate(application.applicationDate) }}</div>
        <div class="row"><strong>当前状态:</strong> <span :class="getStatusClass(application.status)">{{ getStatusText(application.status) }}</span></div>
      </section>

      <section class="section-card review-section">
        <h3>审核情况</h3>
        <div v-if="reviewResult" class="review-summary">
          <p class="review-message">{{ reviewResult.message || '暂无审核说明' }}</p>
          <div v-if="reviewResult.details" class="review-grid">
            <div class="review-item">
              <span class="review-label">材料完整性</span>
              <span class="review-value">{{ formatCompleteness(reviewResult.details.completeness) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">合规性判断</span>
              <span class="review-value">{{ formatCompliance(reviewResult.details.compliance) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">规则审查</span>
              <span class="review-value">{{ formatRuleStatus(fastRules) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">AI 复核</span>
              <span class="review-value">{{ formatAiTrace(aiTrace) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">附件缓存</span>
              <span class="review-value">{{ formatCacheSummary(documentCache) }}</span>
            </div>
            <div class="review-item">
              <span class="review-label">知识库检索</span>
              <span class="review-value">命中 {{ knowledgeHits.length }} 条</span>
            </div>
          </div>

          <div v-if="ruleIssues.length" class="trace-block">
            <h4>规则命中项</h4>
            <ul>
              <li v-for="(item, index) in ruleIssues" :key="index">{{ item.severity }}：{{ item.message }}</li>
            </ul>
          </div>

          <div v-if="complianceDimensions.length" class="trace-block">
            <h4>合规维度</h4>
            <div class="dimension-list">
              <div v-for="item in complianceDimensions" :key="item.code" class="dimension-item">
                <div class="dimension-header">
                  <span>{{ item.name || item.code }}</span>
                  <span :class="getDimensionStatusClass(item.status)" class="dimension-status">{{ formatDimensionStatus(item.status) }}</span>
                </div>
                <ul v-if="Array.isArray(item.findings) && item.findings.length">
                  <li v-for="(finding, index) in item.findings" :key="index">{{ finding.severity }}：{{ finding.message }}</li>
                </ul>
                <p v-else-if="item.reason">{{ item.reason }}</p>
              </div>
            </div>
          </div>

          <div v-if="ragEvidenceItems.length" class="trace-block">
            <h4>法规依据</h4>
            <ul>
              <li v-for="(item, index) in ragEvidenceItems.slice(0, 8)" :key="index">
                {{ item.source || item.dimension }}：{{ item.content }}
              </li>
            </ul>
          </div>

          <div v-if="applicationFormFieldItems.length" class="trace-block">
            <h4>申请书字段识别</h4>
            <div class="field-grid">
              <div v-for="item in applicationFormFieldItems" :key="item.key" class="field-item">
                <span class="field-label">{{ formatFieldLabel(item.key) }}</span>
                <span>{{ item.value }}</span>
              </div>
            </div>
          </div>

          <div v-if="attachmentDocuments.length" class="trace-block">
            <h4>附件解析来源</h4>
            <ul>
              <li v-for="(item, index) in attachmentDocuments.slice(0, 6)" :key="index">
                {{ item.source || item.file_path || '附件' }}：{{ formatReader(item.reader) }}，{{ formatCacheHit(item.document_cache_hit) }}
              </li>
            </ul>
          </div>

          <div v-if="suggestions.length" class="suggestions">
            <h4>修改建议</h4>
            <ul>
              <li v-for="(item, index) in suggestions" :key="index">{{ item }}</li>
            </ul>
          </div>
        </div>
        <div v-else class="review-empty">
          <p>当前申请尚未生成审核结果。</p>
        </div>
      </section>

      <section class="section-card" v-if="displayAttachments.length">
        <h3>附件</h3>
        <ul class="attachment-list">
          <li v-for="(f, idx) in displayAttachments" :key="idx">{{ f }}</li>
        </ul>
      </section>
    </div>
    <div v-else class="no-selection">
      <p>未选择申请。</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  application: { type: Object, default: null }
})

const currentApplication = ref(null)
const reviewResult = ref(null)
const REMOVED_MATERIAL_NAME = '水资源论证相关材料'

const displayAttachments = computed(() => {
  const attachments = currentApplication.value?.attachments || props.application?.attachments
  if (Array.isArray(attachments) && attachments.length) {
    return attachments
  }

  const files = currentApplication.value?.files || props.application?.files
  return Array.isArray(files) ? files : []
})

const suggestions = computed(() => {
  if (Array.isArray(reviewResult.value?.suggestions)) return filterRemovedMaterialItems(reviewResult.value.suggestions)
  const items = reviewResult.value?.details?.suggestions
  return filterRemovedMaterialItems(items)
})

const aiTrace = computed(() => reviewResult.value?.details?.ai_review_trace || {})
const fastRules = computed(() => reviewResult.value?.details?.fast_rules || {})
const documentCache = computed(() => reviewResult.value?.details?.document_cache || {})
const complianceDimensions = computed(() => {
  const items = reviewResult.value?.details?.compliance?.dimensions
  return Array.isArray(items) ? items : []
})
const ragEvidenceItems = computed(() => {
  const evidence = reviewResult.value?.details?.rag_evidence
  if (!evidence || typeof evidence !== 'object') return []
  return Object.entries(evidence).flatMap(([dimension, hits]) => {
    const list = Array.isArray(hits) ? hits : []
    return list.map(item => ({
      dimension,
      source: item?.source,
      content: item?.content,
      score: item?.score
    }))
  }).filter(item => item.content)
})
const applicationFormFieldItems = computed(() => {
  const fields = reviewResult.value?.details?.application_form_fields
  if (!fields || typeof fields !== 'object') return []
  return Object.entries(fields).map(([key, item]) => ({
    key,
    value: item && typeof item === 'object' ? item.value : item
  })).filter(item => item.value)
})
const knowledgeHits = computed(() => {
  const items = reviewResult.value?.knowledge_hits
  return Array.isArray(items) ? items : []
})
const attachmentDocuments = computed(() => {
  const items = reviewResult.value?.details?.attachment_documents
  return Array.isArray(items) ? items : []
})
const ruleIssues = computed(() => {
  const items = fastRules.value?.issues
  if (!Array.isArray(items)) return []

  const seen = new Set()
  return items.filter((item) => {
    const message = String(item?.message || '')
    if (isRemovedMaterialMessage(message)) return false
    const key = `${item?.code || ''}:${message}:${item?.source || ''}`
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
})

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

const formatDetailValue = (value) => {
  if (value === null || value === undefined || value === '') return '暂无'
  if (typeof value === 'string') return value
  if (typeof value === 'boolean') return value ? '是' : '否'
  if (Array.isArray(value)) return value.length ? value.join('；') : '暂无'
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}

const formatCompleteness = (value) => {
  if (!value || typeof value !== 'object') {
    return formatDetailValue(value)
  }

  const missingItemList = filterRemovedMaterialItems(value.missing_items)
  const issueList = filterRemovedMaterialItems(value.issues)
  const missingFieldList = Array.isArray(value.missing_fields) ? value.missing_fields : []
  const hasVisibleProblems = missingItemList.length > 0 || issueList.length > 0 || missingFieldList.length > 0
  const completeText = value.complete === true || value.status === 'PASS' || !hasVisibleProblems ? '完整' : value.complete === false || value.status === 'FAIL' ? '不完整' : '未知'
  const missingItems = missingItemList.length ? `缺少材料：${missingItemList.join('、')}` : ''
  const missingFields = missingFieldList.length ? `缺少字段：${missingFieldList.join('、')}` : ''
  const issues = issueList.length ? issueList.join('；') : ''
  return [completeText, missingItems, missingFields, issues].filter(Boolean).join('；')
}

const formatCompliance = (value) => {
  if (!value || typeof value !== 'object') {
    return formatDetailValue(value)
  }

  const passText = value.status === 'WARNING' ? '有风险，需复核' : value.pass === true || value.status === 'PASS' ? '通过' : value.pass === false || value.status === 'FAIL' ? '不通过' : '未知'
  const violations = Array.isArray(value.violations) && value.violations.length ? value.violations.join('；') : ''
  const warnings = Array.isArray(value.warnings) && value.warnings.length ? `警告：${value.warnings.join('；')}` : ''
  return [passText, violations, warnings].filter(Boolean).join('；')
}

const formatReviewMode = (mode) => {
  const texts = {
    fast: '快速',
    smart: '智能',
    strict: '严格'
  }
  return texts[String(mode || '').toLowerCase()] || mode || '未知'
}

const formatRuleStatus = (rules) => {
  if (!rules || typeof rules !== 'object') return '暂无'
  const statusMap = {
    PASS: '通过',
    WARNING: '有警告',
    BLOCKER: '硬性拦截'
  }
  const status = statusMap[rules.status] || rules.status || '未知'
  const count = Array.isArray(rules.issues) ? rules.issues.length : 0
  return count ? `${status}，${count} 项` : status
}

const formatAiTrace = (trace) => {
  if (!trace || typeof trace !== 'object') return '暂无'
  const mode = formatReviewMode(trace.review_mode)
  const used = trace.used_external_ai ? '已调用 Qwen' : '未调用 Qwen'
  const reason = trace.qwen_decision_reason || trace.fallback_reason
  return [mode, used, reason].filter(Boolean).join('；')
}

const formatCacheSummary = (cache) => {
  if (!cache || typeof cache !== 'object') return '暂无'
  if (cache.enabled === false) return '未启用'
  const total = Number(cache.total_chunks || 0)
  const hits = Number(cache.hit_chunks || 0)
  const misses = Number(cache.miss_chunks || 0)
  if (!total) return '无附件片段'
  return `命中 ${hits} / 未命中 ${misses} / 共 ${total}`
}

const formatReader = (reader) => {
  const texts = {
    'qwen-vl': 'Qwen-VL OCR',
    pdf: 'PDF 解析',
    docx: 'Word 解析',
    doc: 'Word 解析',
    txt: '文本解析',
    md: '文本解析'
  }
  return texts[reader] || reader || '普通解析'
}

const formatCacheHit = (hit) => {
  if (hit === true) return '缓存命中'
  if (hit === false) return '本次解析'
  return '未记录缓存'
}

const formatDimensionStatus = (status) => {
  const texts = {
    PASS: '通过',
    WARNING: '需复核',
    BLOCKER: '硬性问题',
    FAIL: '不通过'
  }
  return texts[status] || status || '未知'
}

const getDimensionStatusClass = (status) => {
  const classes = {
    PASS: 'dimension-pass',
    WARNING: 'dimension-warning',
    BLOCKER: 'dimension-blocker',
    FAIL: 'dimension-blocker'
  }
  return classes[status] || 'dimension-unknown'
}

const formatFieldLabel = (key) => {
  const labels = {
    applicant_name: '申请人',
    applicant_id: '证件号/信用代码',
    legal_representative: '法定代表人',
    project_name: '项目名称',
    water_source_type: '水源类型',
    location: '取水地点',
    intake_location: '取水口位置',
    annual_water_quantity: '年取水量',
    operation_annual_quantity: '运行期年取水量',
    water_use: '取水用途',
    metering_method: '计量方式',
    return_water_quantity: '年退水量',
    drainage_method: '退水方式/排放去向',
    commitment: '承诺内容',
    term: '期限'
  }
  return labels[key] || key
}

const isRemovedMaterialMessage = (value) => String(value || '').includes(REMOVED_MATERIAL_NAME)

const filterRemovedMaterialItems = (items) => {
  if (!Array.isArray(items)) return []
  return items.filter(item => !isRemovedMaterialMessage(item))
}

const maskId = (id) => {
  if (!id) return ''
  return id.slice(0, 3) + '****' + id.slice(-4)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

const parseReviewResult = (payload) => {
  if (!payload) {
    reviewResult.value = null
    return
  }

  if (typeof payload === 'object') {
    reviewResult.value = payload
    return
  }

  try {
    reviewResult.value = JSON.parse(payload)
  } catch (error) {
    reviewResult.value = {
      message: String(payload),
      details: {}
    }
  }
}

const loadApplication = async (applicationId) => {
  if (!applicationId) {
    currentApplication.value = props.application
    parseReviewResult(props.application?.reviewResult)
    return
  }

  try {
    const response = await axios.get(`/api/applications/${applicationId}`)
    currentApplication.value = response.data
    parseReviewResult(response.data?.reviewResult)
  } catch (error) {
    console.error('获取申请详情失败:', error)
    currentApplication.value = props.application
    parseReviewResult(props.application?.reviewResult)
  }
}

watch(() => props.application?.id, (id) => {
  loadApplication(id)
}, { immediate: true })
</script>

<style scoped>
.application-details {
  background: #ffffff;
  padding: 1.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  box-shadow: none;
  max-width: 920px;
  margin: 0 auto;
}

.application-details h2 {
  color: #111827;
  margin-bottom: 1rem;
  font-size: 1.15rem;
}

.section-card {
  padding: 1rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.section-card:last-child {
  border-bottom: none;
}

.section-card h3 {
  margin-bottom: 0.75rem;
  color: #374151;
}

.row {
  margin-bottom: 0.5rem;
}

.review-message {
  margin-bottom: 0.75rem;
  line-height: 1.7;
}

.review-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.review-item {
  background: #f9fafb;
  border-radius: 6px;
  padding: 0.75rem;
}

.review-label {
  display: block;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.review-value {
  white-space: pre-line;
  color: #111827;
}

.suggestions ul,
.attachment-list,
.trace-block ul {
  padding-left: 1.25rem;
}

.suggestions li,
.attachment-list li,
.trace-block li {
  margin-bottom: 0.4rem;
}

.trace-block {
  margin: 0.75rem 0 1rem;
  padding: 0.85rem;
  background: #f9fafb;
  border-radius: 6px;
}

.trace-block h4 {
  margin-bottom: 0.6rem;
  color: #374151;
}

.dimension-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.dimension-item {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.75rem;
}

.dimension-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.dimension-status {
  flex-shrink: 0;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.dimension-pass {
  background: #ecfdf5;
  color: #047857;
}

.dimension-warning {
  background: #fffbeb;
  color: #92400e;
}

.dimension-blocker {
  background: #fef2f2;
  color: #b91c1c;
}

.dimension-unknown {
  background: #f3f4f6;
  color: #4b5563;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.6rem;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.field-label {
  color: #6b7280;
  font-size: 0.85rem;
}

.status-pending,
.status-approved,
.status-rejected,
.status-error {
  background-color: #f3f4f6;
  color: #4b5563;
  padding: 0.2rem 0.45rem;
  border-radius: 4px;
}
</style>

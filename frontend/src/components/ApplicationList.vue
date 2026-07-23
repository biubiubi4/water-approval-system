<template>
  <div class="application-list">
    <div class="list-header">
      <div>
        <p class="section-kicker">Case Registry</p>
        <h2>申请列表</h2>
        <p>共 {{ applications.length }} 条申请，支持按申请人或项目名称检索。</p>
      </div>
      <div class="search-bar">
        <input type="text" v-model="searchQuery" placeholder="搜索申请人或项目名称" />
      </div>
    </div>

    <div class="status-overview">
      <article v-for="item in statusOverview" :key="item.label" :class="['overview-card', item.tone]">
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
      </article>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>申请人</th>
            <th>项目名称</th>
            <th>取水用途</th>
            <th>申请日期</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="app in filteredApplications" :key="app.id">
            <td class="mono">#{{ app.id }}</td>
            <td>
              <strong>{{ app.applicantName }}</strong>
              <span class="subtext">{{ maskId(app.applicantId) }}</span>
            </td>
            <td>{{ app.projectName || '-' }}</td>
            <td>{{ app.waterUse || '-' }}</td>
            <td>{{ formatDate(app.applicationDate) }}</td>
            <td>
              <span :class="getStatusClass(app.status)" class="status-badge">{{ getStatusText(app) }}</span>
            </td>
            <td>
              <div class="actions">
                <button @click="$emit('select-application', app)" class="btn-view">详情</button>
                <button @click="$emit('edit-application', app)" class="btn-edit">编辑</button>
                <button @click="$emit('review-application', app)" class="btn-review">审查</button>
                <button @click="deleteApplication(app.id)" class="btn-delete">删除</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="applications.length === 0" class="empty-state">
      <p>暂无申请记录</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits(['select-application', 'edit-application', 'review-application'])

const applications = ref([])
const searchQuery = ref('')

const filteredApplications = computed(() => {
  if (!searchQuery.value) return applications.value
  return applications.value.filter(app =>
    (app.applicantName || '').toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    (app.projectName || '').toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const statusOverview = computed(() => {
  const total = applications.value.length
  const countByStatus = (status) => applications.value.filter(app => app.status === status).length
  return [
    { label: '全部申请', value: total, tone: 'tone-total' },
    { label: '待审查', value: countByStatus('PENDING'), tone: 'tone-pending' },
    { label: '已通过', value: countByStatus('APPROVED'), tone: 'tone-approved' },
    { label: '需补正', value: countByStatus('REJECTED') + countByStatus('ERROR'), tone: 'tone-risk' }
  ]
})

const maskId = (id) => {
  if (!id) return ''
  return id.slice(0, 3) + '****' + id.slice(-4)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const parseReviewResult = (reviewResult) => {
  if (!reviewResult) return null
  if (typeof reviewResult === 'object') return reviewResult
  try {
    return JSON.parse(reviewResult)
  } catch (error) {
    return null
  }
}

const getRejectedReasons = (application) => {
  const reviewResult = parseReviewResult(application.reviewResult)
  const completeness = reviewResult?.details?.completeness
  const compliance = reviewResult?.details?.compliance
  const reasons = []

  if (completeness && (completeness.complete === false || completeness.status === 'FAIL')) {
    reasons.push('材料不完整')
  }

  if (compliance && (compliance.pass === false || compliance.status === 'FAIL')) {
    reasons.push('合规性有问题')
  }

  return reasons
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

const getStatusText = (application) => {
  const status = application?.status
  const texts = {
    PENDING: '待审核',
    APPROVED: '审核通过',
    REJECTED: '审核未通过',
    ERROR: '审核异常'
  }

  if (status === 'REJECTED') {
    const reasons = getRejectedReasons(application)
    return reasons.length ? `审核未通过（${reasons.join('，')}）` : texts[status]
  }

  return texts[status] || status || '-'
}

const fetchApplications = async () => {
  try {
    const response = await axios.get('/api/applications')
    applications.value = response.data
  } catch (error) {
    console.error('获取申请列表失败:', error)
  }
}

const deleteApplication = async (id) => {
  if (!confirm('确认删除该申请吗？此操作会同时删除上传的附件。')) return
  try {
    await axios.delete(`/api/applications/${id}`)
    await fetchApplications()
    alert('删除成功')
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败: ' + (error.response?.data?.message || error.message))
  }
}

onMounted(fetchApplications)
</script>

<style scoped>
.application-list {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(214, 226, 230, 0.92);
  border-radius: 8px;
  padding: 1.35rem;
  box-shadow: 0 22px 60px rgba(14, 47, 58, 0.12);
  backdrop-filter: blur(12px);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.application-list h2 {
  color: #102633;
  font-size: 1.35rem;
  margin-bottom: 0.25rem;
}

.application-list p {
  color: #60707c;
  font-size: 0.9rem;
}

.section-kicker {
  color: #10879a !important;
  font-size: 0.76rem !important;
  font-weight: 800;
  margin-bottom: 0.25rem;
  text-transform: uppercase;
}

.search-bar {
  width: min(360px, 100%);
}

.search-bar input {
  width: 100%;
  padding: 0.72rem 0.85rem;
  border: 1px solid #cbdbe0;
  border-radius: 8px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10px 24px rgba(15, 42, 52, 0.05);
}

.search-bar input:focus {
  outline: none;
  border-color: #1aa3b7;
  box-shadow: 0 0 0 3px rgba(26, 163, 183, 0.14);
}

.status-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.8rem;
  margin-bottom: 1rem;
}

.overview-card {
  min-height: 86px;
  padding: 0.9rem 1rem;
  border-radius: 8px;
  background: #f7fbfc;
  border: 1px solid #dbe8ec;
}

.overview-card span,
.overview-card strong {
  display: block;
}

.overview-card span {
  color: #61717c;
  font-size: 0.84rem;
}

.overview-card strong {
  margin-top: 0.35rem;
  color: #102633;
  font-size: 1.65rem;
}

.tone-total {
  background: linear-gradient(135deg, #f4fbfc, #edf7f8);
}

.tone-pending {
  background: linear-gradient(135deg, #eef8ff, #f8fcff);
}

.tone-approved {
  background: linear-gradient(135deg, #ecfdf5, #f7fffb);
}

.tone-risk {
  background: linear-gradient(135deg, #fff7ed, #fffaf5);
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #d9e6eb;
  border-radius: 8px;
  background: #ffffff;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.95rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: middle;
}

.table th {
  background-color: #f5f9fa;
  font-weight: 600;
  color: #405360;
  white-space: nowrap;
}

.table tbody tr:hover {
  background: #f4fbfc;
}

.table tbody tr:last-child td {
  border-bottom: none;
}

.mono {
  color: #64748b;
  font-family: Consolas, monospace;
}

.subtext {
  display: block;
  color: #64748b;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.status-pending,
.status-approved,
.status-rejected,
.status-error {
  display: inline-flex;
  align-items: center;
  padding: 0.34rem 0.62rem;
  border-radius: 999px;
  font-size: 0.875rem;
  white-space: nowrap;
}

.status-pending {
  background-color: #f1f5f9;
  color: #475569;
}

.status-approved {
  background-color: #ecfdf5;
  color: #047857;
}

.status-rejected {
  background-color: #fff7ed;
  color: #c2410c;
}

.status-error {
  background-color: #fef2f2;
  color: #b91c1c;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
}

.btn-view,
.btn-edit,
.btn-review,
.btn-delete {
  padding: 0.45rem 0.72rem;
  border: 1px solid #cbdbe0;
  border-radius: 8px;
  cursor: pointer;
  background: #ffffff;
  color: #405360;
  transition: transform 0.18s, border-color 0.18s, background-color 0.18s;
}

.btn-view:hover,
.btn-edit:hover,
.btn-review:hover,
.btn-delete:hover {
  background: #f6fbfc;
  transform: translateY(-1px);
}

.btn-review {
  border-color: #9bdce6;
  color: #067083;
  background: #e9fbfd;
}

.btn-delete {
  border-color: #fecaca;
  color: #b91c1c;
  background: #fff5f5;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}

@media (max-width: 760px) {
  .list-header {
    flex-direction: column;
  }

  .status-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>

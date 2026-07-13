<template>
  <div class="application-list">
    <div class="list-header">
      <div>
        <h2>申请列表</h2>
        <p>共 {{ applications.length }} 条申请，支持按申请人或项目名称检索。</p>
      </div>
      <div class="search-bar">
        <input type="text" v-model="searchQuery" placeholder="搜索申请人或项目名称" />
      </div>
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.25rem;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.06);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.application-list h2 {
  color: #111827;
  font-size: 1.2rem;
  margin-bottom: 0.25rem;
}

.application-list p {
  color: #64748b;
  font-size: 0.9rem;
}

.search-bar {
  width: min(360px, 100%);
}

.search-bar input {
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #ffffff;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.85rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
  vertical-align: middle;
}

.table th {
  background-color: #f8fafc;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.table tbody tr:hover {
  background: #f8fafc;
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
  padding: 0.3rem 0.55rem;
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
  padding: 0.42rem 0.7rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  background: #ffffff;
  color: #374151;
}

.btn-view:hover,
.btn-edit:hover,
.btn-review:hover,
.btn-delete:hover {
  background: #f8fafc;
}

.btn-review {
  border-color: #bfdbfe;
  color: #1d4ed8;
  background: #eff6ff;
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
}
</style>

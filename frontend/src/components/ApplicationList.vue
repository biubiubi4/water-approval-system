<template>
  <div class="application-list">
    <h2>申请列表</h2>
    <div class="search-bar">
      <input type="text" v-model="searchQuery" placeholder="搜索申请人姓名..." />
    </div>
    <table class="table">
      <thead>
        <tr>
          <th>ID</th>
          <th>申请人姓名</th>
          <th>项目名称</th>
          <th>证件号码</th>
          <th>申请日期</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="app in filteredApplications" :key="app.id">
          <td>{{ app.id }}</td>
          <td>{{ app.applicantName }}</td>
          <td>{{ app.projectName || '-' }}</td>
          <td>{{ maskId(app.applicantId) }}</td>
          <td>{{ formatDate(app.applicationDate) }}</td>
          <td>
            <span :class="getStatusClass(app.status)">{{ getStatusText(app) }}</span>
          </td>
          <td>
            <button @click="$emit('select-application', app)" class="btn-view">查看详情</button>
            <button @click="$emit('edit-application', app)" class="btn-edit">编辑</button>
            <button @click="$emit('review-application', app)" class="btn-review">审查/结果</button>
            <button @click="deleteApplication(app.id)" class="btn-delete">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
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
  border-radius: 6px;
  padding: 1.25rem;
}

.application-list h2 {
  margin-bottom: 1rem;
  color: #111827;
  font-size: 1.15rem;
}

.search-bar {
  margin-bottom: 1rem;
}

.search-bar input {
  width: 100%;
  padding: 0.65rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 1rem;
  background: #ffffff;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.table th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #374151;
}

.status-pending,
.status-approved,
.status-rejected,
.status-error {
  background-color: #f3f4f6;
  color: #4b5563;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.btn-view,
.btn-edit,
.btn-review,
.btn-delete {
  padding: 0.4rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  cursor: pointer;
  background: #ffffff;
  color: #374151;
}

.btn-edit,
.btn-review,
.btn-delete {
  margin-left: 0.5rem;
}

.btn-view:hover,
.btn-edit:hover,
.btn-review:hover,
.btn-delete:hover {
  background: #f9fafb;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}
</style>

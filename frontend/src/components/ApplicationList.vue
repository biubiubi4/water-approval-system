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
          <td>{{ maskId(app.applicantId) }}</td>
          <td>{{ formatDate(app.applicationDate) }}</td>
          <td>
            <span :class="getStatusClass(app.status)">{{ getStatusText(app.status) }}</span>
          </td>
          <td>
            <button @click="$emit('select-application', app)" class="btn-view">查看详情</button>
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

const emit = defineEmits(['select-application'])

const applications = ref([])
const searchQuery = ref('')

const filteredApplications = computed(() => {
  if (!searchQuery.value) return applications.value
  return applications.value.filter(app =>
    app.applicantName.toLowerCase().includes(searchQuery.value.toLowerCase())
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

const fetchApplications = async () => {
  try {
    const response = await axios.get('/api/applications')
    applications.value = response.data
  } catch (error) {
    console.error('获取申请列表失败:', error)
  }
}

onMounted(fetchApplications)
</script>

<style scoped>
.application-list {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.application-list h2 {
  margin-bottom: 1rem;
  color: #1e40af;
}

.search-bar {
  margin-bottom: 1rem;
}

.search-bar input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.table th {
  background-color: #f5f7fa;
  font-weight: 600;
}

.status-pending {
  background-color: #fef3c7;
  color: #d97706;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status-approved {
  background-color: #dcfce7;
  color: #16a34a;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status-rejected {
  background-color: #fee2e2;
  color: #dc2626;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.status-error {
  background-color: #e0e7ff;
  color: #4338ca;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.btn-view {
  padding: 0.5rem 1rem;
  background-color: #1e40af;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-view:hover {
  background-color: #1e3a8a;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: #9ca3af;
}
</style>
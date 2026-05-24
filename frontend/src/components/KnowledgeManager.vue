<template>
  <div class="knowledge-manager">
    <section class="hero">
      <div>
        <p class="eyebrow">ChromaDB 可视化管理</p>
        <h2>知识库管理</h2>
        <p class="hero-copy">
          直接查看、检索、编辑和删除向量库中的知识片段，并通过统计图快速掌握数据分布。
        </p>
      </div>
      <div class="hero-actions">
        <button class="btn-secondary" @click="reloadAll" :disabled="loading">刷新数据</button>
        <button class="btn-primary" @click="openCreateDialog">新增知识</button>
      </div>
    </section>

    <section class="parse-workbench">
      <div class="upload-panel">
        <div class="panel-head">
          <div>
            <h3>文件上传与解析</h3>
            <p class="panel-subtitle">先选择文件，再点击解析，系统会自动完成分块并写入向量库。</p>
          </div>
          <div class="panel-actions">
            <button class="btn-secondary" @click="triggerFileInput" :disabled="parseLoading">选择文件</button>
            <button class="btn-primary" @click="handleParseFiles" :disabled="parseLoading || selectedFiles.length === 0">
              {{ parseLoading ? '解析中...' : '开始解析' }}
            </button>
          </div>
        </div>

        <input
          ref="fileInput"
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.md,.csv,.html,.htm,.json"
          class="hidden-input"
          @change="handleFileSelect"
        />

        <div class="drop-zone" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
          <div v-if="selectedFiles.length === 0" class="drop-empty">
            <strong>点击或拖拽文件到此处</strong>
            <span>支持 PDF、Word、TXT、CSV、HTML、JSON</span>
          </div>
          <div v-else class="drop-selected">
            <div class="selected-head">
              <strong>已选择 {{ selectedFiles.length }} 个文件</strong>
              <span>点击“开始解析”后会自动分块并入库</span>
            </div>
            <ul class="selected-file-list">
              <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${index}`">
                <span>{{ file.name }}</span>
                <button type="button" class="text-btn danger" @click.stop="removeSelectedFile(index)">移除</button>
              </li>
            </ul>
          </div>
        </div>

        <div v-if="parseMessage" :class="['inline-message', parseMessageType]">
          {{ parseMessage }}
        </div>
      </div>

      <div v-if="parseResult" class="parse-result-panel">
        <div class="panel-head compact">
          <h3>解析结果</h3>
          <span>{{ parseResult.added || 0 }} 个分块</span>
        </div>

        <div class="parse-summary-grid">
          <article v-for="summary in parseResult.file_summaries || []" :key="summary.file_path" class="parse-summary-card">
            <strong>{{ summary.file_name }}</strong>
            <span>{{ summary.chunk_count }} 个分块</span>
          </article>
        </div>

        <div v-if="(parseResult.failed_files || []).length > 0" class="failed-files">
          <h4>未成功解析的文件</h4>
          <ul>
            <li v-for="item in parseResult.failed_files" :key="item.file">
              <strong>{{ item.file }}</strong>
              <span>{{ item.reason }}</span>
            </li>
          </ul>
        </div>

        <div class="chunk-list" v-if="(parseResult.parsed_documents || []).length > 0">
          <article v-for="chunk in parseResult.parsed_documents" :key="chunk.id || `${chunk.file_path}-${chunk.chunk_index}`" class="chunk-card">
            <div class="chunk-card-head">
              <div>
                <strong>{{ chunk.document_name || chunk.source }}</strong>
                <p>{{ chunk.source }}</p>
              </div>
              <span>分块 {{ chunk.chunk_index || '-' }}</span>
            </div>
            <p class="chunk-preview">{{ chunk.preview || chunk.content }}</p>
            <details>
              <summary>查看完整内容与元数据</summary>
              <pre>{{ prettyMetadata(chunk) }}</pre>
            </details>
          </article>
        </div>
      </div>
    </section>

    <section class="summary-grid" v-if="stats">
      <article class="summary-card accent-blue">
        <span class="summary-label">总记录数</span>
        <strong>{{ stats.total }}</strong>
      </article>
      <article class="summary-card accent-green">
        <span class="summary-label">来源数量</span>
        <strong>{{ stats.unique_sources }}</strong>
      </article>
      <article class="summary-card accent-amber">
        <span class="summary-label">类型数量</span>
        <strong>{{ stats.unique_types }}</strong>
      </article>
      <article class="summary-card accent-slate">
        <span class="summary-label">最近条目</span>
        <strong>{{ stats.latest?.length || 0 }}</strong>
      </article>
    </section>

    <section class="charts" v-if="stats">
      <div class="chart-panel">
        <div class="panel-head">
          <h3>按来源分布</h3>
          <span>{{ stats.sources?.length || 0 }} 个来源</span>
        </div>
        <div class="bars">
          <div v-for="item in sourceBars" :key="item.name" class="bar-row">
            <div class="bar-meta">
              <span class="bar-name">{{ item.name }}</span>
              <span class="bar-count">{{ item.count }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill source-fill" :style="{ width: item.percent + '%' }"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="chart-panel">
        <div class="panel-head">
          <h3>按类型分布</h3>
          <span>{{ stats.types?.length || 0 }} 个类型</span>
        </div>
        <div class="bars">
          <div v-for="item in typeBars" :key="item.name" class="bar-row">
            <div class="bar-meta">
              <span class="bar-name">{{ item.name }}</span>
              <span class="bar-count">{{ item.count }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill type-fill" :style="{ width: item.percent + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="toolbar">
      <div class="toolbar-group">
        <input v-model="filters.q" type="text" placeholder="搜索内容、来源或元数据" />
        <input v-model="filters.source" type="text" placeholder="按来源筛选" />
        <input v-model="filters.recordType" type="text" placeholder="按类型筛选" />
      </div>
      <div class="toolbar-actions">
        <button class="btn-secondary" @click="loadRecords" :disabled="loading">应用筛选</button>
        <button class="btn-ghost" @click="resetFilters">清空</button>
      </div>
    </section>

    <section class="semantic-search-panel">
      <div class="panel-head">
        <h3>语义检索</h3>
        <span>基于向量数据库语义匹配</span>
      </div>

      <div class="semantic-search-form">
        <textarea
          v-model="semanticQuery"
          rows="3"
          placeholder="输入一段业务描述或法规问题，例如：取水许可申请缺少哪些必备材料？"
          @keydown.enter.exact.prevent="runSemanticSearch"
        ></textarea>
        <div class="semantic-actions">
          <label>
            <span>返回条数</span>
            <input v-model.number="semanticTopK" type="number" min="1" max="10" />
          </label>
          <button class="btn-primary" @click="runSemanticSearch" :disabled="semanticLoading">
            {{ semanticLoading ? '检索中...' : '开始语义检索' }}
          </button>
        </div>
      </div>

      <div v-if="semanticLoading" class="loading-state">正在进行语义检索...</div>

      <div v-else-if="semanticSearched && semanticResults.length === 0" class="empty-state">
        未检索到相关文档片段，请尝试调整查询描述。
      </div>

      <div v-else-if="semanticResults.length > 0" class="semantic-result-list">
        <article
          v-for="item in semanticResults"
          :key="`${item.rank}-${item.file_path || item.source || 'manual'}`"
          class="semantic-result-card"
        >
          <div class="semantic-result-head">
            <strong>命中 {{ item.rank }}</strong>
            <span class="semantic-score">相似度 {{ formatSimilarity(item.similarity) }}</span>
          </div>
          <div class="semantic-meta">
            <span>来源：{{ item.source || '-' }}</span>
            <span>分数：{{ formatScore(item.score) }}</span>
            <span v-if="item.page != null">页码：{{ item.page }}</span>
            <span v-if="item.chunk != null">分块：{{ item.chunk }}</span>
          </div>
          <p class="semantic-content">{{ item.content || '无内容' }}</p>
        </article>
      </div>
    </section>

    <section class="batch-toolbar">
      <div class="batch-toolbar-group">
        <span class="batch-summary">已选 {{ selectedRecordIds.length }} 条记录</span>
        <button class="btn-ghost" @click="toggleSelectAll" :disabled="records.length === 0">
          {{ allRecordsSelected ? '取消全选' : '全选' }}
        </button>
        <button class="btn-ghost" @click="clearSelectedRecords" :disabled="selectedRecordIds.length === 0">
          清空选择
        </button>
      </div>
      <div class="batch-toolbar-actions">
        <button class="btn-danger" @click="handleBatchDeleteSelectedRecords" :disabled="batchDeleting || selectedRecordIds.length === 0">
          {{ batchDeleting ? '删除中...' : '批量删除选中记录' }}
        </button>
      </div>
    </section>

    <section class="content-grid">
      <div class="table-panel">
        <div class="panel-head compact">
          <h3>知识记录</h3>
          <span>{{ records.length }} 条</span>
        </div>

        <div v-if="loading" class="loading-state">加载中...</div>

        <div v-else-if="records.length === 0" class="empty-state">
          暂无匹配记录，请尝试新增知识或调整筛选条件。
        </div>

        <div v-else class="table-wrap">
          <table class="records-table">
            <thead>
              <tr>
                <th class="select-col">
                  <input
                    type="checkbox"
                    :checked="allRecordsSelected"
                    :disabled="records.length === 0"
                    @change="toggleSelectAll"
                  />
                </th>
                <th>记录 ID</th>
                <th>来源</th>
                <th>类型</th>
                <th>内容预览</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in records"
                :key="record.id"
                :class="{ selected: selectedRecord?.id === record.id }"
                @click="selectRecord(record)"
              >
                <td class="select-col" @click.stop>
                  <input
                    type="checkbox"
                    :checked="isRecordSelected(record.id)"
                    @change="toggleRecordSelection(record.id)"
                  />
                </td>
                <td>{{ shortId(record.id) }}</td>
                <td>{{ record.source }}</td>
                <td>{{ record.type }}</td>
                <td>
                  <div class="preview-cell">
                    <span>{{ record.preview || '无内容预览' }}</span>
                  </div>
                </td>
                <td>{{ formatDate(record.updated_at || record.created_at) }}</td>
                <td>
                  <div class="action-group" @click.stop>
                    <button class="mini-btn" @click="selectRecord(record)">查看</button>
                    <button class="mini-btn secondary" @click="openEditDialog(record)">编辑</button>
                    <button class="mini-btn danger" @click="removeRecord(record)">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <aside class="detail-panel" v-if="selectedRecord">
        <div class="panel-head compact">
          <h3>记录详情</h3>
          <span>{{ shortId(selectedRecord.id) }}</span>
        </div>
        <dl class="detail-list">
          <div>
            <dt>来源</dt>
            <dd>{{ selectedRecord.source }}</dd>
          </div>
          <div>
            <dt>类型</dt>
            <dd>{{ selectedRecord.type }}</dd>
          </div>
          <div>
            <dt>分块</dt>
            <dd>{{ selectedRecord.chunk || '-' }}</dd>
          </div>
          <div>
            <dt>更新时间</dt>
            <dd>{{ formatDate(selectedRecord.updated_at || selectedRecord.created_at) }}</dd>
          </div>
        </dl>
        <div class="detail-block">
          <h4>内容</h4>
          <pre>{{ selectedRecord.content }}</pre>
        </div>
        <div class="detail-block">
          <h4>元数据</h4>
          <pre>{{ prettyMetadata(selectedRecord.metadata) }}</pre>
        </div>
      </aside>
    </section>

    <div v-if="dialogOpen" class="modal-backdrop" @click.self="closeDialog">
      <div class="modal-card">
        <div class="modal-head">
          <div>
            <p class="eyebrow">{{ dialogMode === 'create' ? '新增记录' : '编辑记录' }}</p>
            <h3>{{ dialogMode === 'create' ? '写入 ChromaDB' : '修改知识片段' }}</h3>
          </div>
          <button class="icon-btn" @click="closeDialog">×</button>
        </div>

        <form class="modal-form" @submit.prevent="submitRecord">
          <label>
            <span>来源</span>
            <input v-model="form.source" type="text" placeholder="例如：manual / 法规文档_1" />
          </label>
          <label>
            <span>类型</span>
            <input v-model="form.type" type="text" placeholder="例如：regulation / manual" />
          </label>
          <label>
            <span>内容</span>
            <textarea v-model="form.content" rows="9" placeholder="请输入知识内容"></textarea>
          </label>
          <label>
            <span>附加元数据（JSON）</span>
            <textarea v-model="form.metadataText" rows="6" placeholder='{"category":"water-law"}'></textarea>
          </label>

          <div class="modal-actions">
            <button type="button" class="btn-ghost" @click="closeDialog">取消</button>
            <button type="submit" class="btn-primary" :disabled="submitting">
              {{ submitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'

const loading = ref(false)
const submitting = ref(false)
const parseLoading = ref(false)
const parseMessage = ref('')
const parseMessageType = ref('')
const selectedFiles = ref([])
const fileInput = ref(null)
const parseResult = ref(null)
const stats = ref(null)
const records = ref([])
const selectedRecord = ref(null)
const dialogOpen = ref(false)
const dialogMode = ref('create')
const editingId = ref(null)
const selectedRecordIds = ref([])
const batchDeleting = ref(false)
const semanticQuery = ref('')
const semanticTopK = ref(4)
const semanticLoading = ref(false)
const semanticResults = ref([])
const semanticSearched = ref(false)

const filters = reactive({
  q: '',
  source: '',
  recordType: ''
})

const form = reactive({
  source: 'manual',
  type: 'manual',
  content: '',
  metadataText: '{}'
})

const maxSourceCount = computed(() => {
  const values = stats.value?.sources || []
  return Math.max(1, ...values.map((item) => item.count || 0))
})

const maxTypeCount = computed(() => {
  const values = stats.value?.types || []
  return Math.max(1, ...values.map((item) => item.count || 0))
})

const sourceBars = computed(() => {
  return (stats.value?.sources || []).map((item) => ({
    ...item,
    percent: Math.round(((item.count || 0) / maxSourceCount.value) * 100)
  }))
})

const typeBars = computed(() => {
  return (stats.value?.types || []).map((item) => ({
    ...item,
    percent: Math.round(((item.count || 0) / maxTypeCount.value) * 100)
  }))
})

const allRecordsSelected = computed(() => {
  return records.value.length > 0 && selectedRecordIds.value.length === records.value.length
})

const shortId = (id) => {
  if (!id) return ''
  return id.length > 14 ? `${id.slice(0, 8)}...${id.slice(-4)}` : id
}

const formatDate = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN')
}

const prettyMetadata = (metadata) => {
  try {
    return JSON.stringify(metadata || {}, null, 2)
  } catch (error) {
    return String(metadata || '')
  }
}

const formatSimilarity = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

const formatScore = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '-'
  return Number(value).toFixed(4)
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const pickedFiles = Array.from(event.target.files || [])
  if (pickedFiles.length === 0) return
  selectedFiles.value = [...selectedFiles.value, ...pickedFiles]
  event.target.value = ''
}

const handleDrop = (event) => {
  const droppedFiles = Array.from(event.dataTransfer.files || [])
  if (droppedFiles.length === 0) return
  selectedFiles.value = [...selectedFiles.value, ...droppedFiles]
}

const removeSelectedFile = (index) => {
  selectedFiles.value.splice(index, 1)
}

const showParseMessage = (message, type = 'success') => {
  parseMessage.value = message
  parseMessageType.value = type
}

const clearParseMessage = () => {
  parseMessage.value = ''
  parseMessageType.value = ''
}

const handleParseFiles = async () => {
  if (selectedFiles.value.length === 0) {
    showParseMessage('请先选择需要解析的文件', 'error')
    return
  }

  parseLoading.value = true
  clearParseMessage()

  try {
    const formData = new FormData()
    selectedFiles.value.forEach((file) => {
      formData.append('files', file)
    })

    const response = await axios.post('/api/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    parseResult.value = response.data || null
    const failedFiles = response.data?.failed_files || []
    if (failedFiles.length > 0) {
      showParseMessage(`${response.data?.message || '文件解析完成'}，部分文件未成功解析`, 'error')
    } else {
      showParseMessage(response.data?.message || '文件解析完成', 'success')
    }
    selectedFiles.value = []
    if (fileInput.value) {
      fileInput.value.value = ''
    }
    await reloadAll()
  } catch (error) {
    console.error('文件解析失败:', error)
    showParseMessage('解析失败: ' + (error.response?.data?.message || error.message), 'error')
  } finally {
    parseLoading.value = false
  }
}

const parseMetadata = () => {
  const raw = form.metadataText?.trim() || '{}'
  if (!raw) return {}
  const parsed = JSON.parse(raw)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('元数据必须是 JSON 对象')
  }
  return parsed
}

const hydrateForm = (record) => {
  form.source = record?.source || 'manual'
  form.type = record?.type || 'manual'
  form.content = record?.content || ''
  form.metadataText = prettyMetadata(record?.metadata || {})
}

const resetFilters = () => {
  filters.q = ''
  filters.source = ''
  filters.recordType = ''
  loadRecords()
}

const openCreateDialog = () => {
  dialogMode.value = 'create'
  editingId.value = null
  hydrateForm({ source: 'manual', type: 'manual', content: '', metadata: { source: 'manual', type: 'manual' } })
  dialogOpen.value = true
}

const openEditDialog = (record) => {
  dialogMode.value = 'edit'
  editingId.value = record.id
  hydrateForm(record)
  dialogOpen.value = true
}

const closeDialog = () => {
  dialogOpen.value = false
}

const selectRecord = (record) => {
  selectedRecord.value = record
}

const isRecordSelected = (recordId) => {
  return selectedRecordIds.value.includes(recordId)
}

const toggleRecordSelection = (recordId) => {
  if (isRecordSelected(recordId)) {
    selectedRecordIds.value = selectedRecordIds.value.filter((id) => id !== recordId)
    return
  }

  selectedRecordIds.value = [...selectedRecordIds.value, recordId]
}

const toggleSelectAll = () => {
  if (allRecordsSelected.value) {
    clearSelectedRecords()
    return
  }

  selectedRecordIds.value = records.value.map((record) => record.id)
}

const clearSelectedRecords = () => {
  selectedRecordIds.value = []
}

const runSemanticSearch = async () => {
  const query = semanticQuery.value.trim()
  if (!query) {
    alert('请输入检索内容')
    return
  }

  semanticLoading.value = true
  semanticSearched.value = true
  try {
    const safeTopK = Math.min(10, Math.max(1, Number(semanticTopK.value) || 4))
    semanticTopK.value = safeTopK
    const response = await axios.get('/api/knowledge/search', {
      params: {
        q: query,
        top_k: safeTopK
      }
    })
    semanticResults.value = response.data?.results || []
  } catch (error) {
    console.error('语义检索失败:', error)
    semanticResults.value = []
    alert('语义检索失败: ' + (error.response?.data?.message || error.message))
  } finally {
    semanticLoading.value = false
  }
}

const loadRecords = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/knowledge/records', {
      params: {
        q: filters.q || undefined,
        source: filters.source || undefined,
        record_type: filters.recordType || undefined
      }
    })
    records.value = response.data.records || []
    stats.value = response.data.summary || { total: 0, sources: [], types: [], latest: [] }
    if (records.value.length === 0) {
      selectedRecord.value = null
    } else if (!selectedRecord.value) {
      selectedRecord.value = records.value[0]
    } else {
      const refreshed = records.value.find((record) => record.id === selectedRecord.value.id)
      selectedRecord.value = refreshed || records.value[0]
    }
    selectedRecordIds.value = selectedRecordIds.value.filter((id) => records.value.some((record) => record.id === id))
  } catch (error) {
    console.error('加载知识记录失败:', error)
    alert('加载知识记录失败: ' + (error.response?.data?.message || error.message))
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await axios.get('/api/knowledge/stats')
    stats.value = response.data.summary || response.data || null
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

const reloadAll = async () => {
  await Promise.all([loadStats(), loadRecords()])
}

const submitRecord = async () => {
  submitting.value = true
  try {
    const metadata = parseMetadata()
    metadata.type = form.type || metadata.type || 'manual'
    metadata.source = form.source || metadata.source || 'manual'

    const payload = {
      content: form.content,
      source: form.source || 'manual',
      metadata
    }

    if (dialogMode.value === 'create') {
      await axios.post('/api/knowledge/records', payload)
    } else {
      await axios.put(`/api/knowledge/records/${editingId.value}`, payload)
    }

    closeDialog()
    await reloadAll()
    alert(dialogMode.value === 'create' ? '新增成功' : '保存成功')
  } catch (error) {
    console.error('保存知识记录失败:', error)
    alert('保存失败: ' + (error.response?.data?.detail || error.response?.data?.message || error.message))
  } finally {
    submitting.value = false
  }
}

const removeRecord = async (record) => {
  if (!confirm(`确认删除记录 ${shortId(record.id)} 吗？`)) return
  try {
    await axios.delete(`/api/knowledge/records/${record.id}`)
    if (selectedRecord.value?.id === record.id) {
      selectedRecord.value = null
    }
    selectedRecordIds.value = selectedRecordIds.value.filter((id) => id !== record.id)
    await reloadAll()
    alert('删除成功')
  } catch (error) {
    console.error('删除知识记录失败:', error)
    alert('删除失败: ' + (error.response?.data?.detail || error.response?.data?.message || error.message))
  }
}

const handleBatchDeleteSelectedRecords = async () => {
  if (selectedRecordIds.value.length === 0) {
    alert('请先勾选要删除的记录')
    return
  }

  if (!confirm(`确认删除已选中的 ${selectedRecordIds.value.length} 条记录吗？`)) return

  batchDeleting.value = true
  try {
    const response = await axios.post('/api/knowledge/records/batch-delete', { ids: selectedRecordIds.value })
    const removed = response.data?.removed ?? 0
    const recordsDeleted = response.data?.records || []
    clearSelectedRecords()
    await reloadAll()
    alert('删除成功')
    if (recordsDeleted.length > 0) {
      console.log('批量删除记录:', recordsDeleted)
    }
  } catch (error) {
    console.error('批量删除失败:', error)
    alert('批量删除失败: ' + (error.response?.data?.message || error.message))
  } finally {
    batchDeleting.value = false
  }
}

onMounted(reloadAll)
</script>

<style scoped>
.knowledge-manager {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-end;
  padding: 1.5rem;
  border-radius: 20px;
  background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 60%, #38bdf8 100%);
  color: white;
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.22);
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-size: 0.75rem;
  opacity: 0.8;
  margin-bottom: 0.35rem;
}

.hero h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.hero-copy {
  max-width: 46rem;
  line-height: 1.7;
  opacity: 0.92;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.parse-workbench {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 1rem;
}

.upload-panel,
.parse-result-panel {
  background: white;
  border-radius: 18px;
  padding: 1.1rem;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
}

.panel-subtitle {
  margin-top: 0.35rem;
  color: #64748b;
  font-size: 0.92rem;
}

.panel-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.hidden-input {
  display: none;
}

.drop-zone {
  margin-top: 1rem;
  border: 1.5px dashed #cbd5e1;
  border-radius: 18px;
  background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
  padding: 1rem;
  cursor: pointer;
}

.drop-empty {
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  color: #475569;
}

.drop-empty strong {
  font-size: 1.05rem;
  color: #0f172a;
}

.drop-selected {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.selected-head {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.selected-head span {
  font-size: 0.9rem;
  color: #64748b;
}

.selected-file-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.selected-file-list li {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  padding: 0.75rem 0.9rem;
  border-radius: 12px;
  background: #f8fafc;
}

.text-btn {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #1d4ed8;
  font-weight: 600;
}

.text-btn.danger {
  color: #dc2626;
}

.inline-message {
  margin-top: 0.9rem;
  padding: 0.8rem 0.95rem;
  border-radius: 12px;
  font-size: 0.95rem;
}

.inline-message.success {
  background: #dcfce7;
  color: #166534;
}

.inline-message.error {
  background: #fee2e2;
  color: #991b1b;
}

.parse-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.8rem;
}

.parse-summary-card {
  padding: 0.85rem 0.9rem;
  border-radius: 14px;
  background: #eff6ff;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.parse-summary-card span {
  color: #475569;
  font-size: 0.92rem;
}

.failed-files {
  margin-top: 1rem;
  padding: 0.9rem;
  border-radius: 14px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.failed-files h4 {
  margin-bottom: 0.65rem;
  color: #9a3412;
}

.failed-files ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.failed-files li {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  background: white;
}

.failed-files li span {
  color: #7c2d12;
  font-size: 0.9rem;
}

.chunk-list {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 620px;
  overflow: auto;
}

.chunk-card {
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.95rem;
  background: #fff;
}

.chunk-card-head {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.chunk-card-head p {
  color: #64748b;
  font-size: 0.9rem;
  margin-top: 0.25rem;
}

.chunk-card-head span {
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 0.8rem;
  white-space: nowrap;
}

.chunk-preview {
  color: #0f172a;
  line-height: 1.7;
}

.chunk-card details {
  margin-top: 0.75rem;
}

.chunk-card summary {
  cursor: pointer;
  color: #1d4ed8;
  font-weight: 600;
}

.chunk-card pre {
  margin-top: 0.75rem;
  padding: 0.85rem;
  border-radius: 12px;
  background: #0f172a;
  color: #e2e8f0;
  overflow: auto;
  white-space: pre-wrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1rem;
}

.summary-card {
  padding: 1.1rem 1.25rem;
  border-radius: 18px;
  color: white;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.12);
}

.summary-card strong {
  display: block;
  margin-top: 0.45rem;
  font-size: 1.8rem;
}

.summary-label {
  font-size: 0.875rem;
  opacity: 0.9;
}

.accent-blue {
  background: linear-gradient(135deg, #2563eb, #0f172a);
}

.accent-green {
  background: linear-gradient(135deg, #059669, #0f766e);
}

.accent-amber {
  background: linear-gradient(135deg, #d97706, #7c2d12);
}

.accent-slate {
  background: linear-gradient(135deg, #475569, #0f172a);
}

.charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.chart-panel,
.table-panel,
.detail-panel {
  background: white;
  border-radius: 18px;
  padding: 1.1rem;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.panel-head h3 {
  font-size: 1.05rem;
  color: #0f172a;
}

.panel-head span {
  color: #64748b;
  font-size: 0.875rem;
}

.compact {
  margin-bottom: 0.75rem;
}

.bars {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.bar-row {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.bar-meta {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  color: #334155;
  font-size: 0.92rem;
}

.bar-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-track {
  height: 10px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: inherit;
}

.source-fill {
  background: linear-gradient(90deg, #2563eb, #38bdf8);
}

.type-fill {
  background: linear-gradient(90deg, #f59e0b, #ef4444);
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.1rem;
  border-radius: 18px;
  background: white;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
  flex-wrap: wrap;
}

.toolbar-group {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  flex: 1;
}

.toolbar-group input,
.modal-form input,
.modal-form textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  font: inherit;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.toolbar-group input:focus,
.modal-form input:focus,
.modal-form textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.toolbar-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.batch-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.1rem;
  border-radius: 18px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.06);
  flex-wrap: wrap;
}

.semantic-search-panel {
  background: white;
  border-radius: 18px;
  padding: 1.1rem;
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.08);
}

.semantic-search-form {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.semantic-search-form textarea {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.75rem 0.9rem;
  font: inherit;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  resize: vertical;
}

.semantic-search-form textarea:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.semantic-actions {
  display: flex;
  gap: 0.75rem;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
}

.semantic-actions label {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  color: #334155;
  font-size: 0.92rem;
}

.semantic-actions input {
  width: 120px;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  padding: 0.65rem 0.75rem;
  font: inherit;
}

.semantic-result-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.9rem;
}

.semantic-result-card {
  border: 1px solid #dbeafe;
  border-radius: 14px;
  padding: 0.9rem;
  background: #f8fbff;
}

.semantic-result-head {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
}

.semantic-score {
  color: #1d4ed8;
  font-weight: 600;
}

.semantic-meta {
  margin-top: 0.45rem;
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  color: #475569;
  font-size: 0.9rem;
}

.semantic-content {
  margin-top: 0.55rem;
  color: #0f172a;
  line-height: 1.65;
  white-space: pre-wrap;
}

.batch-toolbar-group {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.batch-summary {
  font-weight: 700;
  color: #9a3412;
}

.batch-toolbar-actions {
  display: flex;
  align-items: center;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(320px, 0.9fr);
  gap: 1rem;
  align-items: start;
}

.table-wrap {
  overflow: auto;
}

.records-table {
  width: 100%;
  border-collapse: collapse;
}

.records-table th,
.records-table td {
  padding: 0.8rem 0.7rem;
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  vertical-align: top;
}

.select-col {
  width: 44px;
}

.select-col input[type='checkbox'] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.records-table th {
  background: #f8fafc;
  color: #334155;
  font-size: 0.88rem;
}

.records-table tbody tr {
  cursor: pointer;
  transition: background-color 0.2s;
}

.records-table tbody tr:hover,
.records-table tbody tr.selected {
  background: #eff6ff;
}

.preview-cell {
  max-width: 320px;
  color: #475569;
  line-height: 1.55;
}

.action-group {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.mini-btn,
.btn-primary,
.btn-secondary,
.btn-danger,
.btn-ghost,
.icon-btn {
  border: none;
  border-radius: 999px;
  cursor: pointer;
  font: inherit;
}

.mini-btn,
.btn-primary,
.btn-secondary,
.btn-danger,
.btn-ghost {
  padding: 0.55rem 0.95rem;
  transition: transform 0.18s, opacity 0.18s, background-color 0.18s;
}

.mini-btn:hover,
.btn-primary:hover,
.btn-secondary:hover,
.btn-danger:hover,
.btn-ghost:hover,
.icon-btn:hover {
  transform: translateY(-1px);
}

.btn-primary {
  color: white;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
}

.btn-secondary {
  color: #0f172a;
  background: #e2e8f0;
}

.btn-danger {
  color: white;
  background: linear-gradient(135deg, #dc2626, #b91c1c);
}

.btn-ghost {
  color: #334155;
  background: transparent;
  border: 1px solid #cbd5e1;
}

.mini-btn {
  padding: 0.4rem 0.7rem;
  color: white;
  background: #2563eb;
  font-size: 0.85rem;
}

.mini-btn.secondary {
  background: #059669;
}

.mini-btn.danger {
  background: #dc2626;
}

.loading-state,
.empty-state {
  padding: 2rem 1rem;
  text-align: center;
  color: #64748b;
}

.detail-panel {
  position: sticky;
  top: 1rem;
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.detail-list div {
  padding: 0.8rem;
  border-radius: 14px;
  background: #f8fafc;
}

.detail-list dt {
  font-size: 0.78rem;
  color: #64748b;
  margin-bottom: 0.35rem;
}

.detail-list dd {
  color: #0f172a;
  word-break: break-all;
}

.detail-block {
  margin-top: 0.85rem;
}

.detail-block h4 {
  margin-bottom: 0.5rem;
  color: #0f172a;
}

.detail-block pre {
  white-space: pre-wrap;
  word-break: break-word;
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 14px;
  padding: 0.9rem;
  max-height: 240px;
  overflow: auto;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.62);
  display: grid;
  place-items: center;
  z-index: 30;
  padding: 1rem;
}

.modal-card {
  width: min(820px, 100%);
  max-height: 92vh;
  overflow: auto;
  background: white;
  border-radius: 22px;
  padding: 1.1rem;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.26);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.modal-head h3 {
  font-size: 1.3rem;
  color: #0f172a;
}

.icon-btn {
  width: 2.2rem;
  height: 2.2rem;
  background: #e2e8f0;
  color: #0f172a;
  font-size: 1.25rem;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}

.modal-form label {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  color: #334155;
  font-size: 0.92rem;
}

.modal-form textarea {
  resize: vertical;
  min-height: 110px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (max-width: 1100px) {
  .summary-grid,
  .charts,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    position: static;
  }
}

@media (max-width: 760px) {
  .hero,
  .toolbar,
  .modal-head {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-group {
    grid-template-columns: 1fr;
  }

  .detail-list {
    grid-template-columns: 1fr;
  }

  .hero h2 {
    font-size: 1.6rem;
  }
}
</style>
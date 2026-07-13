<template>
  <div class="create-application">
    <div class="page-heading">
      <div>
        <h2>{{ isEdit ? '编辑申请' : '新建申请' }}</h2>
        <p>按标准申请书填写基础信息，可一次上传申请书、身份证明、营业执照、论证报告等多个附件。</p>
      </div>
    </div>

    <form @submit.prevent="submitApplication" class="form">
      <section class="form-section">
        <h3>申请基础信息</h3>
        <div class="form-grid">
          <div class="form-group">
            <label for="applicantName">申请人或申请单位</label>
            <input type="text" id="applicantName" v-model="form.applicantName" required placeholder="例如：惠州市安捷诚表面处理材料有限公司" />
          </div>
          <div class="form-group">
            <label for="applicantId">统一社会信用代码或身份证号码</label>
            <input type="text" id="applicantId" v-model="form.applicantId" required placeholder="请输入统一社会信用代码或身份证号码" />
          </div>
          <div class="form-group">
            <label for="projectName">项目名称</label>
            <input type="text" id="projectName" v-model="form.projectName" required placeholder="例如：环保材料生产项目" />
          </div>
          <div class="form-group">
            <label for="waterUse">取水用途</label>
            <input type="text" id="waterUse" v-model="form.waterUse" required placeholder="例如：工业用水、生活用水、农业用水" />
          </div>
          <div class="form-group wide">
            <label for="location">取水地点</label>
            <input type="text" id="location" v-model="form.location" required placeholder="填写至村/社区或取水口所在位置" />
          </div>
        </div>
      </section>

      <section class="form-section">
        <div class="section-title-row">
          <h3>附件材料</h3>
          <span class="file-count">{{ totalFileCount }} 个文件</span>
        </div>

        <div v-if="isEdit && existingFiles.length > 0" class="existing-files">
          <p>已保存附件</p>
          <ul>
            <li v-for="(f, idx) in existingFiles" :key="idx">{{ f }}</li>
          </ul>
          <span>本次选择的新文件会追加到当前附件列表。</span>
        </div>

        <div
          class="upload-dropzone"
          :class="{ dragging: isDragging }"
          @click="triggerFilePicker"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <input
            ref="fileInput"
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt,.md"
            @change="handleFileChange"
          />
          <div class="upload-icon">+</div>
          <div>
            <strong>点击选择或拖入多个附件</strong>
            <p>建议包含取水许可申请书、身份证明或营业执照、水资源论证相关材料。</p>
          </div>
        </div>

        <ul v-if="selectedFiles.length" class="selected-files">
          <li v-for="(file, index) in selectedFiles" :key="`${file.name}-${file.size}-${index}`">
            <div>
              <strong>{{ file.name }}</strong>
              <span>{{ formatFileSize(file.size) }}</span>
            </div>
            <button type="button" @click="removeFile(index)" class="btn-remove">移除</button>
          </li>
        </ul>
      </section>

      <div class="form-actions">
        <button type="submit" :disabled="isSubmitting" class="btn-submit">
          <span v-if="isSubmitting">提交中...</span>
          <span v-else>{{ isEdit ? '保存修改' : '提交申请' }}</span>
        </button>
        <button v-if="isEdit" type="button" @click="cancelEdit" class="btn-cancel">取消</button>
      </div>
    </form>

    <div v-if="message" :class="messageClass" class="message">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import axios from 'axios'

const emit = defineEmits(['saved'])

const props = defineProps({
  application: {
    type: Object,
    default: null
  }
})

const form = reactive({
  projectName: '',
  applicantName: '',
  applicantId: '',
  waterUse: '',
  location: ''
})

const fileInput = ref(null)
const selectedFiles = ref([])
const existingFiles = ref([])
const isDragging = ref(false)
const isSubmitting = ref(false)
const message = ref('')
const messageType = ref('')

const isEdit = computed(() => !!props.application)
const totalFileCount = computed(() => existingFiles.value.length + selectedFiles.value.length)

const messageClass = computed(() => ({
  'message-success': messageType.value === 'success',
  'message-error': messageType.value === 'error'
}))

function resetForm() {
  form.projectName = ''
  form.applicantName = ''
  form.applicantId = ''
  form.waterUse = ''
  form.location = ''
  selectedFiles.value = []
  existingFiles.value = []
  if (fileInput.value) fileInput.value.value = ''
}

watch(() => props.application, (val) => {
  if (val) {
    form.projectName = val.projectName || ''
    form.applicantName = val.applicantName || ''
    form.applicantId = val.applicantId || ''
    form.waterUse = val.waterUse || ''
    form.location = val.location || ''
    selectedFiles.value = []
    existingFiles.value = Array.isArray(val.files) ? [...val.files] : []
  } else {
    resetForm()
  }
}, { immediate: true })

const triggerFilePicker = () => {
  fileInput.value?.click()
}

const addFiles = (files) => {
  const incoming = Array.from(files || []).filter(file => file && file.name)
  const merged = [...selectedFiles.value]

  incoming.forEach((file) => {
    const exists = merged.some(item => item.name === file.name && item.size === file.size && item.lastModified === file.lastModified)
    if (!exists) merged.push(file)
  })

  selectedFiles.value = merged
}

const handleFileChange = (event) => {
  addFiles(event.target.files)
  if (fileInput.value) fileInput.value.value = ''
}

const handleDrop = (event) => {
  isDragging.value = false
  addFiles(event.dataTransfer.files)
}

const removeFile = (index) => {
  selectedFiles.value = selectedFiles.value.filter((_, itemIndex) => itemIndex !== index)
}

const formatFileSize = (size) => {
  if (!size) return '0 KB'
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

const showMessage = (msg, type) => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
    messageType.value = ''
  }, 5000)
}

const emitSaved = () => {
  emit('saved')
}

const cancelEdit = () => {
  emitSaved()
}

const submitApplication = async () => {
  if (!isEdit.value && selectedFiles.value.length === 0) {
    showMessage('请至少上传一份附件材料', 'error')
    return
  }

  isSubmitting.value = true
  message.value = ''

  const formData = new FormData()
  formData.append('projectName', form.projectName)
  formData.append('applicantName', form.applicantName)
  formData.append('applicantId', form.applicantId)
  formData.append('waterUse', form.waterUse)
  formData.append('location', form.location)

  selectedFiles.value.forEach((file) => {
    formData.append('files', file)
  })

  try {
    if (isEdit.value) {
      await axios.put(`/api/applications/${props.application.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      showMessage('修改已保存', 'success')
    } else {
      const response = await axios.post('/api/applications', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      if (response.status === 201) {
        showMessage('申请提交成功', 'success')
        resetForm()
      }
    }
    emitSaved()
  } catch (error) {
    showMessage('请求失败: ' + (error.response?.data?.message || error.message), 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
.create-application {
  max-width: 960px;
  margin: 0 auto;
}

.page-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.page-heading h2 {
  color: #111827;
  font-size: 1.35rem;
  margin-bottom: 0.35rem;
}

.page-heading p {
  color: #6b7280;
  line-height: 1.6;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1.25rem;
}

.form-section h3 {
  color: #1f2937;
  font-size: 1rem;
  margin-bottom: 1rem;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.file-count {
  color: #2563eb;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  padding: 0.25rem 0.65rem;
  font-size: 0.85rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group.wide {
  grid-column: 1 / -1;
}

.form-group label {
  margin-bottom: 0.45rem;
  font-weight: 600;
  color: #374151;
}

.form-group input {
  padding: 0.72rem 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  background: #ffffff;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

.existing-files {
  margin-bottom: 1rem;
  padding: 0.9rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
}

.existing-files p {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.existing-files ul {
  padding-left: 1.1rem;
  color: #4b5563;
}

.existing-files span {
  display: block;
  margin-top: 0.5rem;
  color: #6b7280;
  font-size: 0.85rem;
}

.upload-dropzone {
  display: flex;
  align-items: center;
  gap: 1rem;
  border: 1px dashed #94a3b8;
  border-radius: 8px;
  padding: 1.25rem;
  background: #f8fafc;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.upload-dropzone.dragging,
.upload-dropzone:hover {
  border-color: #2563eb;
  background: #eff6ff;
}

.upload-dropzone input {
  display: none;
}

.upload-icon {
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2563eb;
  color: #ffffff;
  font-size: 1.4rem;
  font-weight: 600;
}

.upload-dropzone strong {
  display: block;
  color: #111827;
  margin-bottom: 0.3rem;
}

.upload-dropzone p {
  color: #6b7280;
  line-height: 1.5;
}

.selected-files {
  margin-top: 1rem;
  list-style: none;
  display: grid;
  gap: 0.65rem;
}

.selected-files li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 0.75rem 0.9rem;
  background: #ffffff;
}

.selected-files strong {
  display: block;
  color: #111827;
  word-break: break-all;
}

.selected-files span {
  color: #6b7280;
  font-size: 0.85rem;
}

.btn-remove,
.btn-cancel,
.btn-submit {
  border-radius: 6px;
  cursor: pointer;
}

.btn-remove {
  border: 1px solid #fecaca;
  color: #b91c1c;
  background: #fff5f5;
  padding: 0.35rem 0.65rem;
}

.form-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.btn-submit {
  min-width: 150px;
  padding: 0.75rem 1rem;
  background-color: #2563eb;
  color: white;
  border: none;
  font-size: 0.95rem;
  transition: background-color 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #1d4ed8;
}

.btn-submit:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.btn-cancel {
  min-width: 100px;
  padding: 0.72rem 1rem;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;
}

.message {
  margin-top: 1rem;
  padding: 0.85rem;
  border-radius: 6px;
  text-align: center;
}

.message-success {
  background-color: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.message-error {
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

@media (max-width: 720px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-submit,
  .btn-cancel {
    width: 100%;
  }
}
</style>

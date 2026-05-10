<template>
  <div class="create-application">
    <h2>新建申请</h2>
    <form @submit.prevent="submitApplication" class="form">
      <div class="form-group">
        <label for="applicantName">申请人姓名</label>
        <input type="text" id="applicantName" v-model="form.applicantName" required placeholder="请输入申请人姓名" />
      </div>
      <div class="form-group">
        <label for="applicantId">证件号码</label>
        <input type="text" id="applicantId" v-model="form.applicantId" required placeholder="请输入证件号码" />
      </div>
      <div class="form-group">
        <label for="files">上传附件</label>
        <div class="upload-area" @click="triggerFileInput" @dragover.prevent @drop.prevent="handleDrop">
          <input type="file" id="files" ref="fileInput" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" @change="handleFileSelect" style="display: none;" />
          <div v-if="files.length === 0" class="upload-hint">
            <p>点击或拖拽文件到此处上传</p>
            <p class="hint-text">支持 PDF、Word、图片等格式</p>
          </div>
          <div v-else class="file-list">
            <div v-for="(file, index) in files" :key="index" class="file-item">
              <span>{{ file.name }}</span>
              <button type="button" @click="removeFile(index)" class="btn-remove">×</button>
            </div>
          </div>
        </div>
      </div>
      <div class="form-actions">
        <button type="submit" :disabled="isSubmitting" class="btn-submit">
          <span v-if="isSubmitting">提交中...</span>
          <span v-else>提交申请</span>
        </button>
      </div>
    </form>
    <div v-if="message" :class="messageClass" class="message">
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'

const form = reactive({
  applicantName: '',
  applicantId: ''
})

const files = ref([])
const fileInput = ref(null)
const isSubmitting = ref(false)
const message = ref('')
const messageType = ref('')

const messageClass = {
  'message-success': messageType.value === 'success',
  'message-error': messageType.value === 'error'
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  files.value = [...files.value, ...selectedFiles]
}

const handleDrop = (event) => {
  const droppedFiles = Array.from(event.dataTransfer.files)
  files.value = [...files.value, ...droppedFiles]
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const submitApplication = async () => {
  if (files.value.length === 0) {
    showMessage('请至少上传一个附件', 'error')
    return
  }

  isSubmitting.value = true
  message.value = ''

  const formData = new FormData()
  formData.append('applicantName', form.applicantName)
  formData.append('applicantId', form.applicantId)
  
  files.value.forEach(file => {
    formData.append('files', file)
  })

  try {
    const response = await axios.post('/api/applications', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    if (response.status === 201) {
      showMessage('申请提交成功', 'success')
      resetForm()
    }
  } catch (error) {
    showMessage('申请提交失败: ' + (error.response?.data?.message || error.message), 'error')
  } finally {
    isSubmitting.value = false
  }
}

const showMessage = (msg, type) => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
    messageType.value = ''
  }, 5000)
}

const resetForm = () => {
  form.applicantName = ''
  form.applicantId = ''
  files.value = []
}
</script>

<style scoped>
.create-application {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-width: 600px;
  margin: 0 auto;
}

.create-application h2 {
  margin-bottom: 1.5rem;
  color: #1e40af;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #374151;
}

.form-group input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: #1e40af;
}

.upload-hint {
  color: #6b7280;
}

.upload-hint p {
  margin: 0.5rem 0;
}

.hint-text {
  font-size: 0.875rem;
  color: #9ca3af;
}

.file-list {
  text-align: left;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.btn-remove {
  background-color: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.form-actions {
  margin-top: 1rem;
}

.btn-submit {
  width: 100%;
  padding: 0.75rem;
  background-color: #1e40af;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #1e3a8a;
}

.btn-submit:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.message {
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 4px;
  text-align: center;
}

.message-success {
  background-color: #dcfce7;
  color: #16a34a;
}

.message-error {
  background-color: #fee2e2;
  color: #dc2626;
}
</style>
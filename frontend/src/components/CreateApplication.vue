<template>
  <div class="create-application">
    <h2>{{ isEdit ? '编辑申请' : '新建申请' }}</h2>
    <form @submit.prevent="submitApplication" class="form">
      <div class="form-group">
        <label for="projectName">项目名称</label>
        <input type="text" id="projectName" v-model="form.projectName" required placeholder="请输入项目名称" />
      </div>
      <div class="form-group">
        <label for="applicantName">申请人姓名</label>
        <input type="text" id="applicantName" v-model="form.applicantName" required placeholder="请输入申请人姓名" />
      </div>
      <div class="form-group">
        <label for="applicantId">证件号码</label>
        <input type="text" id="applicantId" v-model="form.applicantId" required placeholder="请输入证件号码" />
      </div>
      <div class="form-group">
        <label>附件材料</label>

        <div v-if="isEdit && existingFiles.length > 0" class="existing-files">
          <p class="hint-text">当前已上传的文件：</p>
          <ul>
            <li v-for="(f, idx) in existingFiles" :key="idx">{{ f }}</li>
          </ul>
          <p class="hint-text warning">若需修改附件，请同时上传最新的申请书、身份证和营业执照以替换。</p>
        </div>

        <div class="upload-area-group">
          <div class="specific-upload" @click="triggerSpecificFile('appForm')">
            <span class="upload-title">1. 取水许可申请书 *</span>
            <input type="file" ref="appFormInput" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png" @change="handleSpecificFile($event, 'appForm')" style="display: none;" />
            <div v-if="!fileSlots.appForm" class="upload-hint-sm">点击上传</div>
            <div v-else class="file-item-sm" @click.stop>
              <span>{{ fileSlots.appForm.name }}</span>
              <button type="button" @click.stop="removeSpecificFile('appForm')" class="btn-remove">×</button>
            </div>
          </div>

          <div class="specific-upload" @click="triggerSpecificFile('idCard')">
            <span class="upload-title">2. 法定代表人身份证 *</span>
            <input type="file" ref="idCardInput" accept=".jpg,.jpeg,.png,.pdf" @change="handleSpecificFile($event, 'idCard')" style="display: none;" />
            <div v-if="!fileSlots.idCard" class="upload-hint-sm">点击上传</div>
            <div v-else class="file-item-sm" @click.stop>
              <span>{{ fileSlots.idCard.name }}</span>
              <button type="button" @click.stop="removeSpecificFile('idCard')" class="btn-remove">×</button>
            </div>
          </div>

          <div class="specific-upload" @click="triggerSpecificFile('bizLicense')">
            <span class="upload-title">3. 营业执照 *</span>
            <input type="file" ref="bizLicenseInput" accept=".jpg,.jpeg,.png,.pdf" @change="handleSpecificFile($event, 'bizLicense')" style="display: none;" />
            <div v-if="!fileSlots.bizLicense" class="upload-hint-sm">点击上传</div>
            <div v-else class="file-item-sm" @click.stop>
              <span>{{ fileSlots.bizLicense.name }}</span>
              <button type="button" @click.stop="removeSpecificFile('bizLicense')" class="btn-remove">×</button>
            </div>
          </div>
        </div>
      </div>

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

const form = reactive({
  projectName: '',
  applicantName: '',
  applicantId: ''
})

const fileSlots = reactive({
  appForm: null,
  idCard: null,
  bizLicense: null
})

const appFormInput = ref(null)
const idCardInput = ref(null)
const bizLicenseInput = ref(null)

const isSubmitting = ref(false)
const message = ref('')
const messageType = ref('')
const existingFiles = ref([])

const props = defineProps({
  application: {
    type: Object,
    default: null
  }
})

const isEdit = computed(() => !!props.application)

function resetForm() {
  form.projectName = ''
  form.applicantName = ''
  form.applicantId = ''
  fileSlots.appForm = null
  fileSlots.idCard = null
  fileSlots.bizLicense = null
  existingFiles.value = []
}

watch(() => props.application, (val) => {
  if (val) {
    form.projectName = val.projectName || ''
    form.applicantName = val.applicantName || ''
    form.applicantId = val.applicantId || ''
    existingFiles.value = Array.isArray(val.files) ? [...val.files] : []
  } else {
    resetForm()
  }
}, { immediate: true })

const messageClass = computed(() => ({
  'message-success': messageType.value === 'success',
  'message-error': messageType.value === 'error'
}))

const triggerSpecificFile = (type) => {
  if (type === 'appForm') appFormInput.value?.click()
  if (type === 'idCard') idCardInput.value?.click()
  if (type === 'bizLicense') bizLicenseInput.value?.click()
}

const handleSpecificFile = (event, type) => {
  const file = event.target.files[0]
  if (file) {
    fileSlots[type] = file
  }
}

const removeSpecificFile = (type) => {
  fileSlots[type] = null
  if (type === 'appForm' && appFormInput.value) appFormInput.value.value = ''
  if (type === 'idCard' && idCardInput.value) idCardInput.value.value = ''
  if (type === 'bizLicense' && bizLicenseInput.value) bizLicenseInput.value.value = ''
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
  const newFiles = []
  if (fileSlots.appForm) newFiles.push(fileSlots.appForm)
  if (fileSlots.idCard) newFiles.push(fileSlots.idCard)
  if (fileSlots.bizLicense) newFiles.push(fileSlots.bizLicense)

  const hasAnyNewFile = newFiles.length > 0
  const hasAllNewFiles = newFiles.length === 3

  if (!isEdit.value && !hasAllNewFiles) {
    showMessage('新建申请需上传完整的申请书、身份证和营业执照', 'error')
    return
  }

  if (isEdit.value && hasAnyNewFile && !hasAllNewFiles) {
    showMessage('若要修改附件，请同时上传最新的申请书、身份证和营业执照', 'error')
    return
  }

  isSubmitting.value = true
  message.value = ''

  const formData = new FormData()
  formData.append('projectName', form.projectName)
  formData.append('applicantName', form.applicantName)
  formData.append('applicantId', form.applicantId)

  newFiles.forEach((file) => {
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1.25rem;
  max-width: 600px;
  margin: 0 auto;
}

.create-application h2 {
  margin-bottom: 1.5rem;
  color: #111827;
  font-size: 1.15rem;
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
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 1rem;
  background: #ffffff;
}

.upload-area-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.specific-upload {
  flex: 1;
  min-width: 150px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 1.1rem 0.9rem;
  text-align: center;
  cursor: pointer;
  background-color: #ffffff;
  transition: border-color 0.2s, background-color 0.2s;
}

.specific-upload:hover {
  border-color: #9ca3af;
  background-color: #f9fafb;
}

.upload-title {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #4b5563;
  font-size: 0.95rem;
}

.upload-hint-sm {
  font-size: 0.85rem;
  color: #9ca3af;
}

.file-item-sm {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #1f2937;
  word-break: break-all;
}

.btn-remove {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0 0.5rem;
}

.warning {
  color: #6b7280;
}

.hint-text {
  font-size: 0.875rem;
  color: #9ca3af;
}

.form-actions {
  margin-top: 1rem;
}

.btn-submit {
  width: 100%;
  padding: 0.75rem;
  background-color: #4b5563;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #374151;
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

.message-success,
.message-error {
  background-color: #f3f4f6;
  color: #374151;
}

.btn-cancel {
  margin-top: 0.75rem;
  width: 100%;
  padding: 0.7rem;
  border: 1px solid #d1d5db;
  background: #ffffff;
  color: #374151;
  border-radius: 4px;
  cursor: pointer;
}
</style>

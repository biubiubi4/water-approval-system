<template>
  <div class="app-container" :style="{ '--hero-image': `url(${heroImage})` }">
    <header class="header">
      <div class="header-inner">
        <div class="brand">
          <span class="brand-mark">水</span>
          <div>
            <h1>涉水审批智能审核系统</h1>
            <p>取水许可材料预审、法规检索与 AI 复核工作台</p>
          </div>
        </div>
        <nav class="nav">
          <button @click="currentPage = 'list'" :class="{ active: currentPage === 'list' }">申请总览</button>
          <button @click="newApplication" :class="{ active: currentPage === 'create' }">新建申请</button>
          <button @click="currentPage = 'knowledge'" :class="{ active: currentPage === 'knowledge' }">法规知识库</button>
        </nav>
      </div>
    </header>

    <section class="hero-shell">
      <div class="hero-panel">
        <p class="eyebrow">{{ pageMeta.eyebrow }}</p>
        <h2>{{ pageMeta.title }}</h2>
        <p>{{ pageMeta.description }}</p>
        <div class="hero-metrics">
          <article v-for="metric in pageMeta.metrics" :key="metric.label">
            <strong>{{ metric.value }}</strong>
            <span>{{ metric.label }}</span>
          </article>
        </div>
      </div>
    </section>

    <main class="main-content">
      <ApplicationList v-if="currentPage === 'list'" @select-application="viewDetails" @edit-application="editApplication" @review-application="viewResult" />
      <CreateApplication v-if="currentPage === 'create'" :application="selectedApplication" @saved="onSaved" />
      <ReviewResult v-if="currentPage === 'result'" :application="selectedApplication" />
      <ApplicationDetails v-if="currentPage === 'details'" :application="selectedApplication" />
      <KnowledgeManager v-if="currentPage === 'knowledge'" />
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import ApplicationList from './components/ApplicationList.vue'
import CreateApplication from './components/CreateApplication.vue'
import ReviewResult from './components/ReviewResult.vue'
import ApplicationDetails from './components/ApplicationDetails.vue'
import KnowledgeManager from './components/KnowledgeManager.vue'
import heroImage from './assets/water-governance-hero.png'

const currentPage = ref('list')
const selectedApplication = ref(null)

const pageMetaMap = {
  list: {
    eyebrow: 'Hydro Approval Console',
    title: '一屏掌握取水许可全流程',
    description: '把申请受理、材料校验、规则审查、AI 复核和知识检索聚合在统一工作台，辅助审批人员快速判断风险与补正方向。',
    metrics: [
      { value: 'AI', label: '智能复核' },
      { value: 'RAG', label: '法规检索' },
      { value: 'OCR', label: '附件解析' }
    ]
  },
  create: {
    eyebrow: 'Application Intake',
    title: '标准化采集申请材料',
    description: '通过结构化表单与多附件上传沉淀项目关键信息，为后续自动预审和人工复核提供统一输入。',
    metrics: [
      { value: 'PDF', label: '申请书' },
      { value: 'DOC', label: '论证材料' },
      { value: 'IMG', label: '证照附件' }
    ]
  },
  result: {
    eyebrow: 'AI Review Trace',
    title: '审核结论与证据链并排呈现',
    description: '将材料完整性、合规维度、规则命中、知识库证据和 AI 复核轨迹汇总为可追溯结果。',
    metrics: [
      { value: 'PASS', label: '通过' },
      { value: 'WARN', label: '复核' },
      { value: 'BLOCK', label: '拦截' }
    ]
  },
  details: {
    eyebrow: 'Case Detail',
    title: '申请详情、附件与审查过程留痕',
    description: '围绕单个申请查看基础信息、状态、附件来源和审查明细，便于补正、归档和现场沟通。',
    metrics: [
      { value: 'ID', label: '申请标识' },
      { value: 'Trace', label: '审查轨迹' },
      { value: 'Files', label: '材料清单' }
    ]
  },
  knowledge: {
    eyebrow: 'Knowledge Ops',
    title: '法规知识库运营中心',
    description: '管理向量库中的法规片段、文件解析结果和语义检索命中，为审批审查提供稳定依据。',
    metrics: [
      { value: 'Vector', label: '向量检索' },
      { value: 'Chunks', label: '分块入库' },
      { value: 'Audit', label: '依据沉淀' }
    ]
  }
}

const pageMeta = computed(() => pageMetaMap[currentPage.value] || pageMetaMap.list)

const viewResult = (application) => {
  selectedApplication.value = application
  currentPage.value = 'result'
}

const viewDetails = (application) => {
  selectedApplication.value = application
  currentPage.value = 'details'
}

const editApplication = (application) => {
  selectedApplication.value = application
  currentPage.value = 'create'
}

const onSaved = () => {
  selectedApplication.value = null
  currentPage.value = 'list'
}

const newApplication = () => {
  selectedApplication.value = null
  currentPage.value = 'create'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
}

body {
  font-family: "Microsoft YaHei", "PingFang SC", Arial, Helvetica, sans-serif;
  background: #071a25;
  color: #172033;
}

.app-container {
  min-height: 100vh;
  background:
    linear-gradient(180deg, rgba(5, 22, 33, 0.38) 0, rgba(244, 249, 250, 0.96) 560px, #f4f7f8 100%),
    var(--hero-image) center top / min(1780px, 135vw) auto no-repeat,
    #f4f7f8;
}

.header {
  position: sticky;
  top: 0;
  z-index: 20;
  color: #ffffff;
  background: rgba(6, 27, 39, 0.72);
  border-bottom: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(18px);
  box-shadow: 0 12px 34px rgba(5, 18, 28, 0.22);
}

.header-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0.95rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.brand-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  background: linear-gradient(135deg, #d8f6ff, #47b7c7 55%, #0b5c72);
  color: #052130;
  font-weight: 800;
  box-shadow: 0 12px 24px rgba(36, 189, 208, 0.26);
}

.header h1 {
  font-size: 1.2rem;
  margin-bottom: 0.18rem;
  font-weight: 700;
  color: #ffffff;
}

.header p {
  color: rgba(230, 247, 250, 0.78);
  font-size: 0.92rem;
}

.nav {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.nav button {
  padding: 0.58rem 0.95rem;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.86);
  cursor: pointer;
  transition: background-color 0.2s, border-color 0.2s, transform 0.2s;
}

.nav button:hover,
.nav button.active {
  background: rgba(231, 252, 255, 0.95);
  border-color: rgba(231, 252, 255, 0.95);
  color: #063142;
  transform: translateY(-1px);
}

.hero-shell {
  max-width: 1180px;
  margin: 0 auto;
  padding: 4.3rem 1.5rem 1.6rem;
}

.hero-panel {
  width: min(720px, 100%);
  color: #ffffff;
  text-shadow: 0 2px 20px rgba(0, 0, 0, 0.32);
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  margin-bottom: 0.8rem;
  padding: 0.28rem 0.72rem;
  border-radius: 999px;
  background: rgba(232, 253, 255, 0.18);
  border: 1px solid rgba(232, 253, 255, 0.28);
  color: #e8fdff;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
}

.hero-panel h2 {
  font-size: clamp(2rem, 5vw, 4.2rem);
  line-height: 1.05;
  max-width: 11em;
  margin-bottom: 1rem;
  letter-spacing: 0;
}

.hero-panel p {
  max-width: 42rem;
  color: rgba(246, 253, 255, 0.9);
  line-height: 1.75;
  font-size: 1.02rem;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.75rem;
  width: min(560px, 100%);
  margin-top: 1.35rem;
}

.hero-metrics article {
  min-height: 86px;
  padding: 0.9rem 1rem;
  border-radius: 8px;
  background: rgba(6, 31, 45, 0.54);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(14px);
}

.hero-metrics strong,
.hero-metrics span {
  display: block;
}

.hero-metrics strong {
  font-size: 1.3rem;
  color: #dffcff;
}

.hero-metrics span {
  margin-top: 0.3rem;
  color: rgba(232, 247, 250, 0.76);
  font-size: 0.86rem;
}

.main-content {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 1.5rem 2.2rem;
}

@media (max-width: 760px) {
  .header-inner {
    flex-direction: column;
    align-items: stretch;
  }

  .hero-shell {
    padding-top: 3rem;
  }

  .hero-metrics {
    grid-template-columns: 1fr;
  }
}
</style>

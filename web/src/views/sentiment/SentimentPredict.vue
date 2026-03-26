<template>
  <div class="sentiment-predict">
    <h2 class="page-title">情感预测</h2>

    <el-row :gutter="20">
      <!-- 左侧：输入和预测 -->
      <el-col :span="14">
        <div class="card-box">
          <h3 class="card-title">文本情感预测</h3>
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="5"
            placeholder="请输入要分析的文本，例如小说评论..."
            maxlength="500"
            show-word-limit
          />
          <div class="action-bar">
            <el-button type="primary" @click="handlePredict" :loading="predicting" :disabled="!inputText.trim()">
              <el-icon><MagicStick /></el-icon> 分析情感
            </el-button>
            <el-button @click="fillExample('好看')">示例：正面</el-button>
            <el-button @click="fillExample('差评')">示例：负面</el-button>
          </div>

          <!-- 预测结果 -->
          <div v-if="prediction" class="result-section">
            <div class="result-header">
              <el-tag :type="getLabelType(prediction.label)" effect="dark" size="large">
                {{ prediction.labelText }}
              </el-tag>
              <span class="confidence">置信度分数: {{ prediction.score }}</span>
            </div>

            <!-- 概率分布 -->
            <div class="prob-bars">
              <div class="prob-item">
                <span class="prob-label">正面</span>
                <el-progress :percentage="prediction.probabilities.positive" :stroke-width="20" :text-inside="true" color="#67c23a" />
              </div>
              <div class="prob-item">
                <span class="prob-label">中性</span>
                <el-progress :percentage="prediction.probabilities.neutral" :stroke-width="20" :text-inside="true" color="#909399" />
              </div>
              <div class="prob-item">
                <span class="prob-label">负面</span>
                <el-progress :percentage="prediction.probabilities.negative" :stroke-width="20" :text-inside="true" color="#f56c6c" />
              </div>
            </div>

            <!-- 分词结果 -->
            <div class="tokenize-result" v-if="prediction.words && prediction.words.length > 0">
              <h4>分词结果</h4>
              <div class="word-tags">
                <el-tag v-for="(word, i) in prediction.words" :key="i" size="small" effect="plain" class="word-tag">{{ word }}</el-tag>
              </div>
            </div>

            <!-- 词汇贡献度 -->
            <div class="contributions" v-if="prediction.wordContributions && prediction.wordContributions.length > 0">
              <h4>关键词贡献度</h4>
              <div ref="contribChartRef" class="contrib-chart"></div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：模型信息 -->
      <el-col :span="10">
        <div class="card-box">
          <h3 class="card-title">模型信息</h3>
          <div v-if="modelInfo" class="model-info">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="模型架构">{{ modelInfo.algorithm || modelInfo.model_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="隐藏维度">{{ modelInfo.d_model || '-' }}</el-descriptions-item>
              <el-descriptions-item label="注意力头数">{{ modelInfo.nhead || '-' }}</el-descriptions-item>
              <el-descriptions-item label="编码层数">{{ modelInfo.num_layers || '-' }}</el-descriptions-item>
              <el-descriptions-item label="前馈维度">{{ modelInfo.dim_feedforward || '-' }}</el-descriptions-item>
              <el-descriptions-item label="词汇表大小">{{ modelInfo.vocab_size || '-' }}</el-descriptions-item>
              <el-descriptions-item label="最大长度">{{ modelInfo.max_len || '-' }}</el-descriptions-item>
              <el-descriptions-item label="分类数">{{ modelInfo.num_classes || '-' }}</el-descriptions-item>
              <el-descriptions-item label="中性阈值">{{ modelInfo.neutral_threshold || '-' }}</el-descriptions-item>
              <el-descriptions-item label="运行设备">{{ modelInfo.device || '-' }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>

        <div class="card-box">
          <h3 class="card-title">模型管理</h3>
          <p class="batch-desc">更新模型后，先重置旧标签再批量重新分析，确保所有结果严格来自最新模型</p>
          <div class="manage-btns">
            <el-button type="danger" @click="handleResetLabels" :loading="resetLoading" plain>
              <el-icon><RefreshRight /></el-icon> 1. 重置旧标签
            </el-button>
            <el-button type="warning" @click="handleBatchAnalyze" :loading="batchLoading">
              <el-icon><Operation /></el-icon> 2. 批量重新分析
            </el-button>
            <el-button type="success" @click="handleResetAndAnalyze" :loading="resetAndAnalyzeLoading">
              <el-icon><Promotion /></el-icon> 一键重置+分析
            </el-button>
          </div>
          <div v-if="resetResult" class="batch-result">
            <el-alert :title="resetResult.message" type="warning" show-icon :closable="false" />
          </div>
          <div v-if="batchResult" class="batch-result">
            <el-alert :title="batchResult.message" :type="batchResult.error ? 'error' : 'success'" show-icon :closable="false" />
          </div>
        </div>

        <div class="card-box">
          <h3 class="card-title">快速测试</h3>
          <div class="quick-tests">
            <div v-for="example in examples" :key="example.text" class="test-item" @click="fillAndPredict(example.text)">
              <el-tag :type="example.type" size="small">{{ example.label }}</el-tag>
              <span class="test-text">{{ example.text }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/index'

const inputText = ref('')
const prediction = ref(null)
const predicting = ref(false)
const modelInfo = ref(null)
const batchLoading = ref(false)
const batchResult = ref(null)
const resetLoading = ref(false)
const resetResult = ref(null)
const resetAndAnalyzeLoading = ref(false)
const contribChartRef = ref(null)
let contribChart = null

const examples = [
  { text: '这本书太好看了，情节紧凑，人物刻画生动，强烈推荐！', label: '正面', type: 'success' },
  { text: '一般般吧，没什么特别的，打发时间还行。', label: '中性', type: 'info' },
  { text: '真的很差劲，剧情拖沓，主角无脑，浪费时间。', label: '负面', type: 'danger' },
  { text: '前面写得不错，但是后面越来越水，有点失望。', label: '混合', type: 'warning' },
  { text: '非常精彩的修仙小说，世界观宏大，废寝忘食看完了！', label: '正面', type: 'success' },
  { text: '烂尾了，前面封神后面崩坏，可惜了这个设定。', label: '负面', type: 'danger' }
]

function getLabelType(label) {
  if (label === 'positive') return 'success'
  if (label === 'negative') return 'danger'
  return 'info'
}

function fillExample(type) {
  if (type === '好看') inputText.value = '这本小说写得非常好看，剧情精彩，人物立体，值得反复阅读！'
  else inputText.value = '看不下去了，太无聊了，剧情老套，人设崩坏，差评。'
}

function fillAndPredict(text) {
  inputText.value = text
  handlePredict()
}

async function handlePredict() {
  if (!inputText.value.trim()) return
  predicting.value = true
  prediction.value = null
  try {
    const res = await request.post('/sentiment/predict', { text: inputText.value })
    prediction.value = res.data
    nextTick(() => renderContribChart())
  } catch (e) { /* keep empty */ }
  predicting.value = false
}

function renderContribChart() {
  if (!contribChartRef.value || !prediction.value?.wordContributions) return
  if (contribChart) contribChart.dispose()
  contribChart = echarts.init(contribChartRef.value)

  const data = prediction.value.wordContributions
  const words = data.map(d => d.word).reverse()
  const values = data.map(d => d.contribution).reverse()

  contribChart.setOption({
    tooltip: { trigger: 'axis', formatter: p => `${p[0].name}: ${p[0].value > 0 ? '+' : ''}${p[0].value}` },
    grid: { left: 80, right: 20, top: 10, bottom: 10 },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: words, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { fontSize: 13 } },
    series: [{
      type: 'bar', barWidth: 14,
      data: values.map(v => ({
        value: v,
        itemStyle: { color: v > 0 ? '#67c23a' : v < 0 ? '#f56c6c' : '#909399', borderRadius: v > 0 ? [0, 4, 4, 0] : [4, 0, 0, 4] }
      }))
    }]
  })
}

async function loadModelInfo() {
  try {
    const res = await request.get('/sentiment/model-info')
    modelInfo.value = res.data
  } catch (e) { /* keep empty */ }
}

async function handleBatchAnalyze() {
  batchLoading.value = true
  batchResult.value = null
  try {
    const res = await request.post('/sentiment/batch-analyze')
    batchResult.value = res.data
  } catch (e) { /* keep empty */ }
  batchLoading.value = false
}

async function handleResetLabels() {
  try {
    await ElMessageBox.confirm('确认清除所有评论的情感标签缓存？清除后需重新批量分析。', '重置确认', { type: 'warning' })
  } catch { return }
  resetLoading.value = true
  resetResult.value = null
  batchResult.value = null
  try {
    const res = await request.post('/sentiment/reset-labels')
    resetResult.value = res.data
    ElMessage.success(`已清除 ${res.data.cleared} 条旧标签`)
  } catch (e) { /* keep empty */ }
  resetLoading.value = false
}

async function handleResetAndAnalyze() {
  try {
    await ElMessageBox.confirm('将清除所有旧标签并用最新Transformer模型重新分析全部评论，耗时较长，确认执行？', '一键重置+分析', { type: 'warning' })
  } catch { return }
  resetAndAnalyzeLoading.value = true
  resetResult.value = null
  batchResult.value = null
  try {
    const resetRes = await request.post('/sentiment/reset-labels')
    resetResult.value = resetRes.data
    const batchRes = await request.post('/sentiment/batch-analyze')
    batchResult.value = batchRes.data
    ElMessage.success('全部评论已用最新模型重新分析完成！')
  } catch (e) { /* keep empty */ }
  resetAndAnalyzeLoading.value = false
}

onMounted(() => { loadModelInfo() })
onUnmounted(() => { contribChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.sentiment-predict { padding: $spacing-lg; }
.page-title { font-size: 22px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-lg; }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }

.action-bar { display: flex; gap: $spacing-sm; margin-top: $spacing-md; }

.result-section { margin-top: $spacing-lg; padding-top: $spacing-lg; border-top: 1px solid $border-light; }
.result-header { display: flex; align-items: center; gap: $spacing-md; margin-bottom: $spacing-lg; .confidence { font-size: 14px; color: $text-secondary; } }

.prob-bars { display: flex; flex-direction: column; gap: $spacing-sm; margin-bottom: $spacing-lg; }
.prob-item { display: flex; align-items: center; gap: $spacing-md; .prob-label { width: 40px; font-size: 14px; font-weight: 500; color: $text-primary; flex-shrink: 0; } .el-progress { flex: 1; } }

.tokenize-result { margin-bottom: $spacing-lg; h4 { font-size: 14px; font-weight: 600; margin: 0 0 $spacing-sm; } }
.word-tags { display: flex; flex-wrap: wrap; gap: 4px; .word-tag { font-size: 12px; } }

.contributions { h4 { font-size: 14px; font-weight: 600; margin: 0 0 $spacing-sm; } }
.contrib-chart { width: 100%; height: 300px; }

.batch-desc { font-size: 13px; color: $text-secondary; margin-bottom: $spacing-md; }
.batch-result { margin-top: $spacing-md; }
.manage-btns { display: flex; gap: $spacing-sm; flex-wrap: wrap; margin-bottom: $spacing-sm; }

.quick-tests { display: flex; flex-direction: column; gap: $spacing-sm; }
.test-item {
  display: flex; align-items: flex-start; gap: $spacing-sm; padding: $spacing-sm $spacing-md;
  border-radius: $border-radius-sm; background: $bg-color; cursor: pointer; transition: all 0.2s;
  &:hover { background: #edf0f5; transform: translateX(4px); }
  .test-text { font-size: 13px; color: $text-regular; line-height: 1.5; }
}
</style>

<template>
  <div class="export-page">
    <div class="page-header">
      <h2 class="page-title">导出报告</h2>
      <p class="page-desc">将平台可视化分析结果导出为PDF报告，包含图表截图和文字说明</p>
    </div>

    <div class="card-box">
      <h3 class="card-title">报告预览与导出</h3>

      <div class="export-actions">
        <el-button type="primary" size="large" @click="generateReport" :loading="generating">
          <el-icon><Download /></el-icon> 生成并下载PDF报告
        </el-button>
        <el-button size="large" @click="loadReportData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新数据
        </el-button>
      </div>

      <el-alert v-if="!reportData" title="点击「生成并下载PDF报告」开始生成" type="info" show-icon :closable="false" style="margin-top: 16px;" />
    </div>

    <!-- 隐藏的图表渲染区 -->
    <div class="hidden-charts" ref="hiddenArea">
      <div ref="categoryChartRef" style="width: 800px; height: 400px;"></div>
      <div ref="sentimentChartRef" style="width: 600px; height: 400px;"></div>
      <div ref="hotBooksChartRef" style="width: 800px; height: 400px;"></div>
    </div>

    <!-- 报告预览 -->
    <div v-if="reportData" class="report-preview">
      <div class="card-box preview-section">
        <h3 class="section-title">1. 平台概览</h3>
        <p class="section-desc">{{ descriptions.overview }}</p>
        <el-row :gutter="16">
          <el-col :span="6" v-for="metric in overviewMetrics" :key="metric.label">
            <div class="metric-card">
              <div class="metric-value">{{ metric.value }}</div>
              <div class="metric-label">{{ metric.label }}</div>
            </div>
          </el-col>
        </el-row>
      </div>

      <div class="card-box preview-section">
        <h3 class="section-title">2. 分类排行</h3>
        <p class="section-desc">{{ descriptions.categoryRank }}</p>
        <el-table :data="(reportData.categoryRank || []).slice(0, 15)" stripe size="small" style="width: 100%">
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="categoryName" label="分类名称" />
          <el-table-column prop="bookCount" label="书籍数量" align="center" />
        </el-table>
      </div>

      <div class="card-box preview-section">
        <h3 class="section-title">3. 标签词云</h3>
        <p class="section-desc">{{ descriptions.tagCloud }}</p>
        <div class="tag-preview">
          <el-tag v-for="tag in (reportData.tagCloud || []).slice(0, 20)" :key="tag.name" size="small" effect="plain" class="preview-tag">
            {{ tag.name }} ({{ tag.value }})
          </el-tag>
        </div>
      </div>

      <div class="card-box preview-section">
        <h3 class="section-title">4. 情感分析</h3>
        <p class="section-desc">{{ descriptions.sentiment }}</p>
      </div>

      <div class="card-box preview-section">
        <h3 class="section-title">5. 热门书籍 Top 10</h3>
        <el-table :data="reportData.hotBooks || []" stripe size="small" style="width: 100%">
          <el-table-column type="index" label="#" width="60" />
          <el-table-column prop="bookName" label="书名" />
          <el-table-column prop="author" label="作者" />
          <el-table-column prop="score" label="评分" width="80" align="center" />
          <el-table-column prop="readCount" label="阅读量" width="120" align="center">
            <template #default="{ row }">{{ Number(row.readCount).toLocaleString() }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { jsPDF } from 'jspdf'
import request from '@/api/index'
import { ElMessage } from 'element-plus'

const reportData = ref(null)
const descriptions = ref({})
const loading = ref(false)
const generating = ref(false)
const overviewMetrics = ref([])

const hiddenArea = ref(null)
const categoryChartRef = ref(null)
const sentimentChartRef = ref(null)
const hotBooksChartRef = ref(null)
let categoryChart = null
let sentimentChart = null
let hotBooksChart = null

async function loadReportData() {
  loading.value = true
  try {
    const res = await request.get('/export/report-data')
    reportData.value = res.data
    descriptions.value = res.data.descriptions || {}

    const ov = res.data.overview || {}
    overviewMetrics.value = [
      { label: '总小说数', value: Number(ov.totalNovel || 0).toLocaleString() },
      { label: '已完结', value: String(ov.todayUpdates || 0) },
      { label: '注册用户', value: Number(ov.activeUsers || 0).toLocaleString() },
      { label: '平均评分', value: String(ov.averageScore || 0) }
    ]
  } catch (e) { /* keep empty */ }
  loading.value = false
}

function renderHiddenCharts() {
  // 分类柱状图
  if (categoryChartRef.value && reportData.value?.categoryRank) {
    categoryChart = echarts.init(categoryChartRef.value)
    const data = reportData.value.categoryRank.slice(0, 15)
    categoryChart.setOption({
      grid: { left: 100, right: 20, top: 10, bottom: 10 },
      xAxis: { type: 'value', show: false },
      yAxis: { type: 'category', data: data.map(d => d.categoryName).reverse(), axisLabel: { fontSize: 14 } },
      series: [{ type: 'bar', data: data.map(d => d.bookCount).reverse(), barWidth: 16, itemStyle: { color: '#409eff', borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', fontSize: 12 } }]
    })
  }

  // 情感饼图
  if (sentimentChartRef.value && reportData.value?.sentimentDistribution) {
    sentimentChart = echarts.init(sentimentChartRef.value)
    const sd = reportData.value.sentimentDistribution
    sentimentChart.setOption({
      color: ['#67c23a', '#909399', '#f56c6c'],
      series: [{ type: 'pie', radius: ['35%', '65%'], label: { fontSize: 14, formatter: '{b}\n{d}%' }, data: [
        { value: sd.positive, name: '正面' }, { value: sd.neutral, name: '中性' }, { value: sd.negative, name: '负面' }
      ]}]
    })
  }

  // 热门书籍柱状图
  if (hotBooksChartRef.value && reportData.value?.hotBooks) {
    hotBooksChart = echarts.init(hotBooksChartRef.value)
    const books = reportData.value.hotBooks.slice(0, 10)
    hotBooksChart.setOption({
      grid: { left: 120, right: 20, top: 10, bottom: 10 },
      xAxis: { type: 'value', show: false },
      yAxis: { type: 'category', data: books.map(b => b.bookName).reverse(), axisLabel: { fontSize: 13 } },
      series: [{ type: 'bar', data: books.map(b => b.readCount).reverse(), barWidth: 14, itemStyle: { color: '#e6a23c', borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', fontSize: 11, formatter: p => Number(p.value).toLocaleString() } }]
    })
  }
}

async function generateReport() {
  if (!reportData.value) {
    await loadReportData()
  }
  if (!reportData.value) {
    ElMessage.error('无法加载报告数据')
    return
  }

  generating.value = true

  await nextTick()
  renderHiddenCharts()

  // 等待图表渲染
  await new Promise(resolve => setTimeout(resolve, 500))

  try {
    const doc = new jsPDF('p', 'mm', 'a4')
    const pageWidth = 210
    const margin = 15
    const contentWidth = pageWidth - margin * 2
    let y = margin

    // 标题
    doc.setFontSize(22)
    doc.setFont('helvetica', 'bold')
    doc.text('Novel Big Data Platform Report', pageWidth / 2, y + 10, { align: 'center' })
    y += 20
    doc.setFontSize(12)
    doc.setFont('helvetica', 'normal')
    doc.text(new Date().toLocaleDateString('zh-CN'), pageWidth / 2, y, { align: 'center' })
    y += 15

    // 分隔线
    doc.setDrawColor(64, 158, 255)
    doc.setLineWidth(0.5)
    doc.line(margin, y, pageWidth - margin, y)
    y += 10

    // 1. 概览
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('1. Platform Overview', margin, y)
    y += 8
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')

    const ov = reportData.value.overview || {}
    const overviewText = `Total Novels: ${ov.totalNovel} | Completed: ${ov.todayUpdates} | Users: ${ov.activeUsers} | Avg Score: ${ov.averageScore}`
    doc.text(overviewText, margin, y)
    y += 12

    // 2. 分类排行图
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('2. Category Distribution', margin, y)
    y += 5

    if (categoryChart) {
      const imgData = categoryChart.getDataURL({ type: 'png', pixelRatio: 2 })
      doc.addImage(imgData, 'PNG', margin, y, contentWidth, contentWidth * 0.5)
      y += contentWidth * 0.5 + 5
    }

    // 3. 情感分析
    doc.addPage()
    y = margin
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('3. Sentiment Analysis', margin, y)
    y += 5

    if (sentimentChart) {
      const imgData = sentimentChart.getDataURL({ type: 'png', pixelRatio: 2 })
      doc.addImage(imgData, 'PNG', margin + 20, y, contentWidth * 0.6, contentWidth * 0.4)
      y += contentWidth * 0.4 + 5
    }

    const sd = reportData.value.sentimentDistribution || {}
    doc.setFontSize(10)
    doc.setFont('helvetica', 'normal')
    doc.text(`Positive: ${sd.positiveRate}% | Neutral: ${sd.neutralRate}% | Negative: ${sd.negativeRate}% (Total: ${sd.total} comments)`, margin, y)
    y += 15

    // 4. 热门书籍
    doc.setFontSize(16)
    doc.setFont('helvetica', 'bold')
    doc.text('4. Top 10 Hot Books', margin, y)
    y += 5

    if (hotBooksChart) {
      const imgData = hotBooksChart.getDataURL({ type: 'png', pixelRatio: 2 })
      doc.addImage(imgData, 'PNG', margin, y, contentWidth, contentWidth * 0.5)
      y += contentWidth * 0.5 + 5
    }

    // 保存
    doc.save('novel-platform-report.pdf')
    ElMessage.success('PDF报告已生成并下载')
  } catch (e) {
    ElMessage.error('报告生成失败: ' + e.message)
  }

  generating.value = false
}

onMounted(() => { loadReportData() })
onUnmounted(() => { categoryChart?.dispose(); sentimentChart?.dispose(); hotBooksChart?.dispose() })
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.export-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header { margin-bottom: $spacing-lg; .page-title { font-size: 22px; font-weight: 700; color: $text-primary; margin: 0 0 6px 0; } .page-desc { font-size: 13px; color: $text-secondary; margin: 0; } }
.card-box { background: $bg-white; border-radius: $border-radius-md; box-shadow: $box-shadow-light; padding: $spacing-lg; margin-bottom: $spacing-lg; }
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-md; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }

.export-actions { display: flex; gap: $spacing-md; }

.hidden-charts { position: absolute; left: -9999px; top: -9999px; }

.report-preview { margin-top: $spacing-lg; }
.preview-section { .section-title { font-size: 18px; font-weight: 600; color: $text-primary; margin-bottom: $spacing-sm; } .section-desc { font-size: 14px; color: $text-secondary; line-height: 1.6; margin-bottom: $spacing-md; } }

.metric-card { text-align: center; padding: $spacing-md; background: $bg-color; border-radius: $border-radius-md; .metric-value { font-size: 24px; font-weight: 700; color: $primary-color; } .metric-label { font-size: 12px; color: $text-secondary; margin-top: 4px; } }

.tag-preview { display: flex; flex-wrap: wrap; gap: $spacing-xs; .preview-tag { font-size: 12px; } }
</style>

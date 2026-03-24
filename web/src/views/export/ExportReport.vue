<template>
  <div class="export-page">
    <div class="page-header">
      <h2 class="page-title">导出报告</h2>
      <p class="page-desc">生成专业的小说大数据分析报告，包含图表、数据表格及深度分析</p>
    </div>

    <div class="card-box">
      <h3 class="card-title">报告操作</h3>
      <div class="export-actions">
        <el-button type="primary" size="large" @click="generatePDF" :loading="generating">
          <el-icon><Download /></el-icon> 生成并下载PDF报告
        </el-button>
        <el-button size="large" @click="loadReportData" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新数据
        </el-button>
      </div>
      <el-alert v-if="!reportData" title="点击「刷新数据」加载报告预览，确认后生成PDF" type="info" show-icon :closable="false" style="margin-top: 16px;" />
    </div>

    <!-- ===== 报告预览（同时作为 html2canvas 截图源） ===== -->
    <div v-if="reportData" class="report-preview-wrapper">

      <!-- 第1页：封面 -->
      <div class="report-section" ref="sectionCover">
        <div class="cover-page">
          <div class="cover-decoration">
            <div class="cover-circle cover-circle-1"></div>
            <div class="cover-circle cover-circle-2"></div>
            <div class="cover-circle cover-circle-3"></div>
          </div>
          <div class="cover-icon">&#128218;</div>
          <h1 class="cover-title">小说大数据分析报告</h1>
          <p class="cover-subtitle">Novel Big Data Analytics Report</p>
          <div class="cover-divider"></div>
          <div class="cover-meta">
            <div class="cover-meta-item">
              <span class="cover-meta-label">报告日期：</span>
              <span class="cover-meta-value">{{ currentDate }}</span>
            </div>
            <div class="cover-meta-item">
              <span class="cover-meta-label">数据来源：</span>
              <span class="cover-meta-value">小说大数据分析平台</span>
            </div>
            <div class="cover-meta-item">
              <span class="cover-meta-label">数据规模：</span>
              <span class="cover-meta-value">{{ formatNumber(overview.totalNovel) }} 部小说 · {{ formatNumber(sentiment.total) }} 条评论</span>
            </div>
          </div>
          <div class="cover-footer"><p>— 本报告由系统自动生成 —</p></div>
        </div>
      </div>

      <!-- 第2页：平台概览 -->
      <div class="report-section" ref="sectionOverview">
        <div class="section-header">
          <span class="section-number">01</span>
          <div>
            <h2 class="section-title">平台概览</h2>
            <p class="section-subtitle">Platform Overview</p>
          </div>
        </div>
        <div class="section-body">
          <p class="analysis-text">{{ descriptions.overview || '以下为平台核心数据指标总览，涵盖小说规模、用户活跃度及内容质量。' }}</p>

          <div class="metrics-grid">
            <div class="metric-card metric-blue">
              <div class="metric-icon-box blue">&#128214;</div>
              <div class="metric-info">
                <div class="metric-value">{{ formatNumber(overview.totalNovel) }}</div>
                <div class="metric-label">总小说数</div>
              </div>
            </div>
            <div class="metric-card metric-green">
              <div class="metric-icon-box green">&#9989;</div>
              <div class="metric-info">
                <div class="metric-value">{{ formatNumber(overview.todayUpdates) }}</div>
                <div class="metric-label">已完结</div>
              </div>
            </div>
            <div class="metric-card metric-orange">
              <div class="metric-icon-box orange">&#128100;</div>
              <div class="metric-info">
                <div class="metric-value">{{ formatNumber(overview.activeUsers) }}</div>
                <div class="metric-label">注册用户</div>
              </div>
            </div>
            <div class="metric-card metric-red">
              <div class="metric-icon-box red">&#11088;</div>
              <div class="metric-info">
                <div class="metric-value">{{ overview.averageScore }}</div>
                <div class="metric-label">平均评分</div>
              </div>
            </div>
          </div>

          <div class="insight-box">
            <div class="insight-icon">&#128202;</div>
            <div class="insight-content">
              <strong>平台洞察：</strong>
              平台已收录 <em>{{ formatNumber(overview.totalNovel) }}</em> 部小说，
              其中已完结作品 <em>{{ formatNumber(overview.todayUpdates) }}</em> 部，
              注册用户数达 <em>{{ formatNumber(overview.activeUsers) }}</em> 人。
              全站平均评分 <em>{{ overview.averageScore }}</em> 分，整体内容质量良好。
            </div>
          </div>

          <h3 class="chart-title">分类分布图</h3>
          <div class="chart-container" ref="categoryChartRef" style="width: 100%; height: 420px;"></div>
        </div>
      </div>

      <!-- 第3页：内容分析 -->
      <div class="report-section" ref="sectionContent">
        <div class="section-header">
          <span class="section-number">02</span>
          <div>
            <h2 class="section-title">内容分析</h2>
            <p class="section-subtitle">Content Analysis</p>
          </div>
        </div>
        <div class="section-body">
          <p class="analysis-text">{{ descriptions.categoryRank || '以下为小说分类排行及标签热度分析，揭示当前网络文学的类型分布特征。' }}</p>

          <h3 class="chart-title">分类排行（前15）</h3>
          <table class="report-table">
            <thead>
              <tr>
                <th style="width: 60px;">排名</th>
                <th>分类名称</th>
                <th style="width: 100px;">书籍数量</th>
                <th>占比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(cat, index) in categoryTop15" :key="cat.categoryName">
                <td>
                  <span class="rank-badge" :class="{ 'rank-1': index === 0, 'rank-2': index === 1, 'rank-3': index === 2 }">
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="category-name">{{ cat.categoryName }}</td>
                <td class="text-center">{{ cat.bookCount }}</td>
                <td>
                  <div class="bar-cell">
                    <div class="bar-fill" :style="{ width: categoryBarWidth(cat.bookCount) + '%' }"></div>
                    <span class="bar-label">{{ categoryPercent(cat.bookCount) }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="sub-section">
            <h3 class="chart-title">标签热度词云</h3>
            <p class="analysis-text">{{ descriptions.tagCloud || '标签词云反映了当前最受关注的内容主题与创作方向。' }}</p>
            <div class="tag-cloud">
              <span v-for="(tag, index) in tagCloudData" :key="tag.name" class="cloud-tag" :style="getTagStyle(tag, index)">
                {{ tag.name }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 第4页：情感分析 -->
      <div class="report-section" ref="sectionSentiment">
        <div class="section-header">
          <span class="section-number">03</span>
          <div>
            <h2 class="section-title">情感分析</h2>
            <p class="section-subtitle">Sentiment Analysis</p>
          </div>
        </div>
        <div class="section-body">
          <p class="analysis-text">{{ descriptions.sentiment || '基于NLP情感分析算法，对全站评论进行正面/中性/负面分类。' }}</p>

          <div class="sentiment-layout">
            <div class="sentiment-chart-wrap">
              <div class="chart-container" ref="sentimentChartRef" style="width: 100%; height: 300px;"></div>
            </div>
            <div class="sentiment-stats">
              <div class="sentiment-stat-item positive">
                <div class="stat-dot"></div>
                <div class="stat-info">
                  <span class="stat-name">正面评价</span>
                  <span class="stat-rate">{{ sentiment.positiveRate || 0 }}%</span>
                </div>
              </div>
              <div class="sentiment-stat-item neutral">
                <div class="stat-dot"></div>
                <div class="stat-info">
                  <span class="stat-name">中性评价</span>
                  <span class="stat-rate">{{ sentiment.neutralRate || 0 }}%</span>
                </div>
              </div>
              <div class="sentiment-stat-item negative">
                <div class="stat-dot"></div>
                <div class="stat-info">
                  <span class="stat-name">负面评价</span>
                  <span class="stat-rate">{{ sentiment.negativeRate || 0 }}%</span>
                </div>
              </div>
              <div class="sentiment-stat-item total">
                <div class="stat-dot"></div>
                <div class="stat-info">
                  <span class="stat-name">评论总计</span>
                  <span class="stat-value">{{ formatNumber(sentiment.total) }} 条</span>
                </div>
              </div>
            </div>
          </div>

          <div class="insight-box">
            <div class="insight-icon">&#128172;</div>
            <div class="insight-content">
              <strong>情感洞察：</strong>
              平台共采集读者评论 <em>{{ formatNumber(sentiment.total) }}</em> 条，
              其中正面评价占比 <em>{{ sentiment.positiveRate || 0 }}%</em>，
              中性评价占比 <em>{{ sentiment.neutralRate || 0 }}%</em>，
              负面评价仅占 <em>{{ sentiment.negativeRate || 0 }}%</em>。
              整体读者情感倾向积极，平台内容质量获得广泛认可。
            </div>
          </div>

          <h3 class="chart-title">口碑排行榜（正面评价率前10）</h3>
          <table class="report-table">
            <thead>
              <tr>
                <th style="width: 60px;">排名</th>
                <th>书籍名称</th>
                <th style="width: 140px;">正面评价率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in reputationTop10" :key="index">
                <td>
                  <span class="rank-badge" :class="{ 'rank-1': index === 0, 'rank-2': index === 1, 'rank-3': index === 2 }">
                    {{ index + 1 }}
                  </span>
                </td>
                <td>{{ item.bookName }}</td>
                <td>
                  <div class="bar-cell">
                    <div class="bar-fill bar-fill-green" :style="{ width: item.positiveRate + '%' }"></div>
                    <span class="bar-label">{{ item.positiveRate }}%</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 第5页：热门书籍 -->
      <div class="report-section" ref="sectionHotBooks">
        <div class="section-header">
          <span class="section-number">04</span>
          <div>
            <h2 class="section-title">热门书籍榜单</h2>
            <p class="section-subtitle">Hot Books Ranking</p>
          </div>
        </div>
        <div class="section-body">
          <p class="analysis-text">根据阅读量、评分等综合指标，选取平台最受欢迎的10部作品，反映当前阅读趋势与用户偏好。</p>

          <h3 class="chart-title">热门书籍 Top 10</h3>
          <table class="report-table">
            <thead>
              <tr>
                <th style="width: 60px;">排名</th>
                <th>书籍名称</th>
                <th>作者</th>
                <th style="width: 80px;">评分</th>
                <th style="width: 120px;">阅读量</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(book, index) in hotBooksTop10" :key="index">
                <td>
                  <span class="rank-badge" :class="{ 'rank-1': index === 0, 'rank-2': index === 1, 'rank-3': index === 2 }">
                    {{ index + 1 }}
                  </span>
                </td>
                <td class="book-name">{{ book.bookName }}</td>
                <td class="text-secondary">{{ book.author }}</td>
                <td class="text-center">
                  <span class="score-badge">{{ book.score }}</span>
                </td>
                <td class="text-center">{{ formatNumber(book.readCount) }}</td>
              </tr>
            </tbody>
          </table>

          <h3 class="chart-title">阅读量对比</h3>
          <div class="chart-container" ref="hotBooksChartRef" style="width: 100%; height: 380px;"></div>

          <div class="conclusion-box">
            <h3 class="conclusion-title">报告总结</h3>
            <div class="conclusion-content">
              <p>本报告基于小说大数据分析平台的全量数据，从平台概览、内容分类、读者情感、热门榜单四个维度进行了全面分析。主要发现如下：</p>
              <ul>
                <li>平台已收录 <em>{{ formatNumber(overview.totalNovel) }}</em> 部小说，内容生态丰富。</li>
                <li>分类分布呈头部集中态势，前三大类目合计占比达 <em>{{ topThreePercent }}%</em>。</li>
                <li>读者情感整体偏向积极，正面评价率高达 <em>{{ sentiment.positiveRate || 0 }}%</em>。</li>
                <li>热门榜单中，<em>{{ hotBooksTop10[0]?.bookName || '-' }}</em> 以 <em>{{ formatNumber(hotBooksTop10[0]?.readCount || 0) }}</em> 阅读量位居榜首。</li>
              </ul>
              <p class="conclusion-footer">— 小说大数据分析平台 · {{ currentDate }} —</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { jsPDF } from 'jspdf'
import html2canvas from 'html2canvas'
import request from '@/api/index'
import { ElMessage } from 'element-plus'
import { Download, Refresh } from '@element-plus/icons-vue'

const reportData = ref(null)
const descriptions = ref({})
const loading = ref(false)
const generating = ref(false)

const categoryChartRef = ref(null)
const sentimentChartRef = ref(null)
const hotBooksChartRef = ref(null)

const sectionCover = ref(null)
const sectionOverview = ref(null)
const sectionContent = ref(null)
const sectionSentiment = ref(null)
const sectionHotBooks = ref(null)

let categoryChart = null
let sentimentChart = null
let hotBooksChart = null

const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`
})

const overview = computed(() => reportData.value?.overview || {})
const sentiment = computed(() => reportData.value?.sentimentDistribution || {})
const categoryTop15 = computed(() => (reportData.value?.categoryRank || []).slice(0, 15))
const tagCloudData = computed(() => (reportData.value?.tagCloud || []).slice(0, 30))
const hotBooksTop10 = computed(() => (reportData.value?.hotBooks || []).slice(0, 10))
const reputationTop10 = computed(() => (reportData.value?.reputationRanking || []).slice(0, 10))

const maxCategoryCount = computed(() => {
  if (!categoryTop15.value.length) return 1
  return Math.max(...categoryTop15.value.map(c => c.bookCount))
})

const topThreePercent = computed(() => {
  const total = overview.value.totalNovel || 1
  const top3 = categoryTop15.value.slice(0, 3).reduce((s, c) => s + (c.bookCount || 0), 0)
  return ((top3 / total) * 100).toFixed(1)
})

function formatNumber(num) {
  return Number(num || 0).toLocaleString()
}

function categoryBarWidth(count) {
  return ((count / maxCategoryCount.value) * 100).toFixed(1)
}

function categoryPercent(count) {
  const total = overview.value.totalNovel || 1
  return ((count / total) * 100).toFixed(1)
}

const tagColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']

function getTagStyle(tag, index) {
  const maxVal = Math.max(...tagCloudData.value.map(t => t.value), 1)
  const ratio = tag.value / maxVal
  const fontSize = 13 + Math.round(ratio * 18)
  return {
    fontSize: fontSize + 'px',
    color: tagColors[index % tagColors.length],
    opacity: 0.7 + ratio * 0.3,
    fontWeight: ratio > 0.6 ? '700' : '400'
  }
}

async function loadReportData() {
  loading.value = true
  try {
    const res = await request.get('/export/report-data')
    reportData.value = res.data
    descriptions.value = res.data?.descriptions || {}
    await nextTick()
    renderCharts()
    ElMessage.success('报告数据加载成功')
  } catch (e) {
    ElMessage.error('加载报告数据失败')
  }
  loading.value = false
}

function renderCharts() {
  renderCategoryChart()
  renderSentimentChart()
  renderHotBooksChart()
}

function renderCategoryChart() {
  if (!categoryChartRef.value || !reportData.value?.categoryRank) return
  if (categoryChart) categoryChart.dispose()
  categoryChart = echarts.init(categoryChartRef.value)
  const data = reportData.value.categoryRank.slice(0, 15)
  categoryChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 110, right: 40, top: 10, bottom: 20 },
    xAxis: { type: 'value', axisLabel: { color: '#909399', fontSize: 12 }, splitLine: { lineStyle: { color: '#f0f0f0' } } },
    yAxis: {
      type: 'category', data: data.map(d => d.categoryName).reverse(),
      axisLabel: { color: '#303133', fontSize: 13 }, axisLine: { show: false }, axisTick: { show: false }
    },
    series: [{
      type: 'bar', data: data.map(d => d.bookCount).reverse(), barWidth: 18,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#409eff' }, { offset: 1, color: '#67c23a' }])
      },
      label: { show: true, position: 'right', fontSize: 12, color: '#606266' }
    }]
  })
}

function renderSentimentChart() {
  if (!sentimentChartRef.value || !reportData.value?.sentimentDistribution) return
  if (sentimentChart) sentimentChart.dispose()
  sentimentChart = echarts.init(sentimentChartRef.value)
  const sd = reportData.value.sentimentDistribution
  sentimentChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}：{c} 条（{d}%）' },
    color: ['#67c23a', '#e6a23c', '#f56c6c'],
    series: [{
      type: 'pie', radius: ['40%', '70%'], center: ['50%', '50%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { fontSize: 14, color: '#303133', formatter: '{b}\n{d}%', lineHeight: 20 },
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } },
      data: [
        { value: sd.positive, name: '正面评价' },
        { value: sd.neutral, name: '中性评价' },
        { value: sd.negative, name: '负面评价' }
      ]
    }]
  })
}

function renderHotBooksChart() {
  if (!hotBooksChartRef.value || !reportData.value?.hotBooks) return
  if (hotBooksChart) hotBooksChart.dispose()
  hotBooksChart = echarts.init(hotBooksChartRef.value)
  const books = reportData.value.hotBooks.slice(0, 10)
  hotBooksChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 140, right: 50, top: 10, bottom: 20 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#909399', fontSize: 11, formatter: val => val >= 10000 ? (val / 10000).toFixed(0) + '万' : val },
      splitLine: { lineStyle: { color: '#f0f0f0' } }
    },
    yAxis: {
      type: 'category', data: books.map(b => b.bookName).reverse(),
      axisLabel: { color: '#303133', fontSize: 12, width: 120, overflow: 'truncate' },
      axisLine: { show: false }, axisTick: { show: false }
    },
    series: [{
      type: 'bar', data: books.map(b => b.readCount).reverse(), barWidth: 16,
      itemStyle: {
        borderRadius: [0, 6, 6, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#e6a23c' }, { offset: 1, color: '#f56c6c' }])
      },
      label: { show: true, position: 'right', fontSize: 11, color: '#606266', formatter: p => Number(p.value).toLocaleString() }
    }]
  })
}

async function generatePDF() {
  if (!reportData.value) await loadReportData()
  if (!reportData.value) {
    ElMessage.error('无法加载报告数据')
    return
  }

  generating.value = true
  ElMessage.info('正在生成PDF报告，请稍候……')

  await nextTick()
  renderCharts()
  await new Promise(resolve => setTimeout(resolve, 800))

  try {
    const sections = [sectionCover.value, sectionOverview.value, sectionContent.value, sectionSentiment.value, sectionHotBooks.value]
    const doc = new jsPDF('p', 'mm', 'a4')
    const pageWidth = 210
    const pageHeight = 297
    const margin = 8
    const contentWidth = pageWidth - margin * 2
    const maxH = pageHeight - margin * 2

    for (let i = 0; i < sections.length; i++) {
      const section = sections[i]
      if (!section) continue

      const canvas = await html2canvas(section, {
        scale: 2, useCORS: true, backgroundColor: '#ffffff', logging: false, allowTaint: true
      })

      const imgData = canvas.toDataURL('image/jpeg', 0.92)
      const imgW = contentWidth
      const imgH = (canvas.height / canvas.width) * contentWidth

      if (i > 0) doc.addPage()

      if (imgH <= maxH) {
        doc.addImage(imgData, 'JPEG', margin, margin, imgW, imgH)
      } else {
        let remaining = imgH
        let srcY = 0
        let page = 0
        while (remaining > 0) {
          if (page > 0) doc.addPage()
          const sliceH = Math.min(maxH, remaining)
          const srcSliceH = (sliceH / imgH) * canvas.height
          const sliceCanvas = document.createElement('canvas')
          sliceCanvas.width = canvas.width
          sliceCanvas.height = srcSliceH
          const ctx = sliceCanvas.getContext('2d')
          ctx.fillStyle = '#ffffff'
          ctx.fillRect(0, 0, sliceCanvas.width, sliceCanvas.height)
          ctx.drawImage(canvas, 0, srcY, canvas.width, srcSliceH, 0, 0, sliceCanvas.width, srcSliceH)
          doc.addImage(sliceCanvas.toDataURL('image/jpeg', 0.92), 'JPEG', margin, margin, imgW, sliceH)
          srcY += srcSliceH
          remaining -= sliceH
          page++
        }
      }
    }

    doc.save('小说大数据分析报告.pdf')
    ElMessage.success('PDF报告已生成并下载')
  } catch (e) {
    console.error(e)
    ElMessage.error('报告生成失败：' + e.message)
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
.card-title { font-size: 16px; font-weight: 600; color: $text-primary; margin: 0 0 $spacing-md 0; padding-left: $spacing-sm; border-left: 3px solid $primary-color; }
.export-actions { display: flex; gap: $spacing-md; }

.report-preview-wrapper { margin-top: $spacing-lg; }

.report-section {
  background: #ffffff; border-radius: $border-radius-lg; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: $spacing-xl; overflow: hidden;
  font-family: 'PingFang SC', 'Microsoft YaHei', 'SimHei', sans-serif;
}

/* 封面 */
.cover-page {
  position: relative; min-height: 680px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; padding: 80px 60px;
  background: linear-gradient(135deg, #f8fbff 0%, #eef5ff 50%, #f0f9f4 100%); overflow: hidden;
}
.cover-decoration { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.cover-circle { position: absolute; border-radius: 50%; }
.cover-circle-1 { width: 300px; height: 300px; top: -80px; right: -60px; background: radial-gradient(circle, rgba(64, 158, 255, 0.08) 0%, transparent 70%); }
.cover-circle-2 { width: 200px; height: 200px; bottom: -40px; left: -40px; background: radial-gradient(circle, rgba(103, 194, 58, 0.08) 0%, transparent 70%); }
.cover-circle-3 { width: 160px; height: 160px; top: 50%; left: 60%; background: radial-gradient(circle, rgba(230, 162, 60, 0.06) 0%, transparent 70%); }
.cover-icon { margin-bottom: 40px; font-size: 60px; position: relative; z-index: 1; }
.cover-title { font-size: 42px; font-weight: 800; color: #303133; margin: 0 0 12px 0; letter-spacing: 4px; z-index: 1; }
.cover-subtitle { font-size: 18px; color: #909399; margin: 0 0 40px 0; letter-spacing: 2px; font-weight: 300; z-index: 1; }
.cover-divider { width: 80px; height: 3px; background: linear-gradient(90deg, #409eff, #67c23a); border-radius: 2px; margin-bottom: 40px; z-index: 1; }
.cover-meta { display: flex; flex-direction: column; gap: 16px; z-index: 1; }
.cover-meta-item { text-align: center; .cover-meta-label { font-size: 13px; color: #909399; margin-right: 12px; } .cover-meta-value { font-size: 15px; color: #303133; font-weight: 500; } }
.cover-footer { position: absolute; bottom: 40px; width: 100%; text-align: center; p { font-size: 13px; color: #c0c4cc; letter-spacing: 2px; margin: 0; } }

/* 章节头 */
.section-header {
  display: flex; align-items: center; gap: 20px; padding: 32px 40px 24px;
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%); border-bottom: 1px solid #f0f2f5;
}
.section-number { font-size: 48px; font-weight: 800; background: linear-gradient(135deg, #409eff, #67c23a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1; }
.section-title { font-size: 26px; font-weight: 700; color: #303133; margin: 0 0 4px 0; }
.section-subtitle { font-size: 13px; color: #c0c4cc; margin: 0; letter-spacing: 1px; }
.section-body { padding: 32px 40px 40px; }

.analysis-text { font-size: 14px; color: #606266; line-height: 1.8; margin: 0 0 24px 0; padding-left: 12px; border-left: 3px solid #e4e7ed; }

/* 指标卡片 */
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 32px; }
.metric-card {
  display: flex; align-items: center; gap: 16px; padding: 24px 20px; border-radius: 12px;
  &.metric-blue { background: linear-gradient(135deg, #f0f7ff, #e8f4ff); }
  &.metric-green { background: linear-gradient(135deg, #f0faf0, #e8f8e8); }
  &.metric-orange { background: linear-gradient(135deg, #fef8f0, #fdf3e0); }
  &.metric-red { background: linear-gradient(135deg, #fff0f0, #fee8e8); }
}
.metric-icon-box {
  width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 24px;
  &.blue { background: rgba(64, 158, 255, 0.12); }
  &.green { background: rgba(103, 194, 58, 0.12); }
  &.orange { background: rgba(230, 162, 60, 0.12); }
  &.red { background: rgba(245, 108, 108, 0.12); }
}
.metric-info { .metric-value { font-size: 28px; font-weight: 800; color: #303133; line-height: 1.2; } .metric-label { font-size: 13px; color: #909399; margin-top: 4px; } }

/* 洞察框 */
.insight-box { display: flex; gap: 16px; padding: 20px 24px; background: linear-gradient(135deg, #fafcff, #f5f8ff); border: 1px solid #e8efff; border-radius: 10px; margin: 28px 0; }
.insight-icon { font-size: 28px; flex-shrink: 0; line-height: 1.6; }
.insight-content { font-size: 14px; color: #606266; line-height: 1.8; strong { color: #303133; } em { font-style: normal; color: #409eff; font-weight: 600; } }

/* 图表 */
.chart-title { font-size: 16px; font-weight: 600; color: #303133; margin: 28px 0 16px; padding-left: 12px; border-left: 3px solid #409eff; }
.chart-container { border: 1px solid #f0f2f5; border-radius: 8px; background: #fafbfc; }

/* 表格 */
.report-table {
  width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; margin-bottom: 8px;
  thead tr { background: #f5f7fa;
    th { padding: 12px 16px; text-align: left; color: #909399; font-weight: 600; font-size: 12px; letter-spacing: 0.5px; border-bottom: 2px solid #ebeef5;
      &:first-child { border-radius: 8px 0 0 0; } &:last-child { border-radius: 0 8px 0 0; }
    }
  }
  tbody tr { transition: background 0.2s; &:hover { background: #fafbfc; } &:nth-child(even) { background: #fafcff; }
    td { padding: 11px 16px; border-bottom: 1px solid #f0f2f5; color: #303133; }
  }
}
.text-center { text-align: center; }
.text-secondary { color: #909399; }
.category-name { font-weight: 500; }
.book-name { font-weight: 600; }

.rank-badge {
  display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px;
  border-radius: 8px; font-size: 13px; font-weight: 700; background: #f0f2f5; color: #909399;
  &.rank-1 { background: linear-gradient(135deg, #ffd700, #ffb800); color: #fff; }
  &.rank-2 { background: linear-gradient(135deg, #c0c0c0, #a8a8a8); color: #fff; }
  &.rank-3 { background: linear-gradient(135deg, #cd7f32, #b8742e); color: #fff; }
}
.score-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 13px; font-weight: 700; background: linear-gradient(135deg, #fff7e6, #fff3d6); color: #e6a23c; border: 1px solid #fde2b0; }

.bar-cell { position: relative; height: 22px; background: #f5f7fa; border-radius: 11px; overflow: hidden; }
.bar-fill { position: absolute; left: 0; top: 0; height: 100%; background: linear-gradient(90deg, #409eff, #66b1ff); border-radius: 11px; transition: width 0.6s ease; }
.bar-fill-green { background: linear-gradient(90deg, #67c23a, #85d35e); }
.bar-label { position: relative; z-index: 1; display: flex; align-items: center; height: 100%; padding-left: 10px; font-size: 12px; font-weight: 600; color: #303133; }

.tag-cloud { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 18px; padding: 24px; background: #fafbfc; border-radius: 10px; border: 1px solid #f0f2f5; min-height: 100px; }
.cloud-tag { display: inline-block; padding: 4px 0; line-height: 1.4; }

.sub-section { margin-top: 36px; }

.sentiment-layout { display: flex; gap: 32px; align-items: center; margin-bottom: 16px; }
.sentiment-chart-wrap { flex: 1; min-width: 0; }
.sentiment-stats { width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; }
.sentiment-stat-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 10px; background: #fafbfc;
  &.positive { .stat-dot { background: #67c23a; } .stat-rate { color: #67c23a; } }
  &.neutral { .stat-dot { background: #e6a23c; } .stat-rate { color: #e6a23c; } }
  &.negative { .stat-dot { background: #f56c6c; } .stat-rate { color: #f56c6c; } }
  &.total { .stat-dot { background: #409eff; } background: #f0f7ff; }
}
.stat-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.stat-info { display: flex; flex-direction: column; gap: 2px;
  .stat-name { font-size: 12px; color: #909399; }
  .stat-value { font-size: 15px; font-weight: 700; color: #303133; }
  .stat-rate { font-size: 20px; font-weight: 800; }
}

.conclusion-box { margin-top: 36px; border: 2px solid #e8efff; border-radius: 12px; overflow: hidden; }
.conclusion-title { font-size: 18px; font-weight: 700; color: #fff; margin: 0; padding: 16px 28px; background: linear-gradient(135deg, #409eff, #3a8ee6); }
.conclusion-content {
  padding: 28px; font-size: 14px; color: #606266; line-height: 1.9;
  p { margin: 0 0 16px; }
  ul { margin: 0 0 20px; padding-left: 20px; li { margin-bottom: 10px; } }
  em { font-style: normal; color: #409eff; font-weight: 600; }
}
.conclusion-footer { text-align: center; color: #c0c4cc !important; font-size: 13px !important; letter-spacing: 2px; }
</style>

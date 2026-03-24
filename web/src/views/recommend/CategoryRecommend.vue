<template>
  <div class="category-recommend-page">
    <div class="page-header">
      <h2 class="page-title">同类别推荐</h2>
      <p class="page-desc">根据小说类别为你推荐同类型的优质作品</p>
    </div>

    <!-- 流动小说名河流 -->
    <div class="novel-river" v-if="riverNames.length > 0">
      <div v-for="(lane, idx) in riverLanes" :key="idx" class="river-lane"
        :style="{ animationDuration: (35 + idx * 12) + 's', animationDirection: idx % 2 === 0 ? 'normal' : 'reverse' }">
        <span v-for="(name, ni) in lane" :key="ni" class="river-name"
          :style="{ '--delay': (ni * 0.5) + 's', fontSize: (13 + Math.random() * 6) + 'px' }">{{ name }}</span>
        <span v-for="(name, ni) in lane" :key="'d' + ni" class="river-name"
          :style="{ fontSize: (13 + Math.random() * 6) + 'px' }">{{ name }}</span>
      </div>
    </div>

    <!-- 类别选择器 -->
    <div class="category-selector">
      <el-radio-group v-model="activeCategory" size="large" @change="handleCategoryChange">
        <el-radio-button v-for="cat in categoryList" :key="cat" :value="cat">{{ cat }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 河流图 -->
    <div class="card-box">
      <h3 class="card-title">类别热度河流图</h3>
      <div ref="riverChartRef" class="river-chart"></div>
    </div>

    <!-- 小说卡片 -->
    <el-row :gutter="20" class="novel-grid">
      <el-col :xs="12" :sm="8" :md="6" v-for="(novel, index) in currentNovels" :key="novel.bookId">
        <div class="novel-card" @click="$emit('open-novel', novel.bookId)">
          <div class="card-top-bar">
            <div class="card-avatar" :style="{ background: avatarColors[index % avatarColors.length] }">
              {{ novel.bookName.charAt(0) }}
            </div>
            <div class="card-info">
              <div class="card-name" :title="novel.bookName">{{ novel.bookName }}</div>
              <div class="card-author">{{ novel.author }}</div>
            </div>
            <div class="card-score">{{ novel.score }}</div>
          </div>
          <div class="card-bottom">
            <div class="card-meta">
              <el-icon><Connection /></el-icon>
              {{ novel.category }} · {{ novel.wordNumber ? (novel.wordNumber / 10000).toFixed(0) + '万字' : '未知' }}
            </div>
            <div class="card-tags" v-if="novel.tags">
              <el-tag v-for="tag in novel.tags.split(',').slice(0, 3)" :key="tag" size="small" effect="plain" round>{{ tag.trim() }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { Connection } from '@element-plus/icons-vue'
import request from '@/api/index'

const avatarColors = [
  'linear-gradient(135deg, #667eea, #764ba2)',
  'linear-gradient(135deg, #f093fb, #f5576c)',
  'linear-gradient(135deg, #4facfe, #00f2fe)',
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)',
  'linear-gradient(135deg, #fccb90, #d57eeb)',
  'linear-gradient(135deg, #e0c3fc, #8ec5fc)'
]

const categoryList = ref([])
const activeCategory = ref('')
const currentNovels = ref([])
const riverNames = ref([])
const categoryRankData = ref([])

const riverChartRef = ref(null)
let riverChart = null

// 将小说名字分成多个泳道
const riverLanes = computed(() => {
  const names = riverNames.value
  if (names.length === 0) return []
  const laneCount = 4
  const lanes = Array.from({ length: laneCount }, () => [])
  names.forEach((name, i) => { lanes[i % laneCount].push(name) })
  return lanes
})

async function loadCategory(category) {
  try {
    const params = category ? { category } : {}
    const res = await request.get('/recommend/category', { params })
    const data = res.data || {}
    if (!categoryList.value.length && data.categories) {
      categoryList.value = data.categories
    }
    if (!activeCategory.value && data.currentCategory) {
      activeCategory.value = data.currentCategory
    }
    currentNovels.value = data.books || []
    riverNames.value = (data.books || []).map(b => b.bookName)
  } catch (e) { /* keep empty */ }
}

async function loadCategoryRank() {
  try {
    const res = await request.get('/stats/category-rank')
    categoryRankData.value = res.data || []
    nextTick(() => initRiverChart())
  } catch (e) { /* keep empty */ }
}

function initRiverChart() {
  if (!riverChartRef.value || categoryRankData.value.length === 0) return
  if (riverChart) riverChart.dispose()
  riverChart = echarts.init(riverChartRef.value)

  const topCats = categoryRankData.value.slice(0, 10)
  const timeSteps = ['2024-01-01', '2024-03-01', '2024-05-01', '2024-07-01', '2024-09-01', '2024-11-01', '2025-01-01', '2025-03-01']
  const riverData = []

  topCats.forEach(cat => {
    const base = cat.bookCount || 1
    const seed = cat.categoryName.charCodeAt(0) + (cat.categoryName.charCodeAt(1) || 0)
    timeSteps.forEach((t, i) => {
      const variation = Math.sin(i * Math.PI / 3.5 + seed * 0.1) * base * 0.35
      riverData.push([t, Math.max(1, Math.round(base + variation)), cat.categoryName])
    })
  })

  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#409eff']

  riverChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: params => {
        if (params.data) {
          return `<strong>${params.data[2]}</strong><br/>时间: ${params.data[0]}<br/>热度: ${params.data[1]}`
        }
        return ''
      }
    },
    singleAxis: {
      top: 50, bottom: 50, type: 'time',
      axisLabel: { fontSize: 13, color: '#606266', formatter: '{yyyy}/{MM}' },
      axisTick: { show: false },
      axisPointer: { animation: true, label: { show: true } }
    },
    color: colors,
    series: [{
      type: 'themeRiver',
      emphasis: { itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,0,0,0.3)' } },
      label: { show: true, fontSize: 11 },
      data: riverData
    }]
  })
}

function handleCategoryChange() {
  loadCategory(activeCategory.value)
}

const handleResize = () => { riverChart?.resize() }

onMounted(() => {
  loadCategory()
  loadCategoryRank()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  riverChart?.dispose()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.category-recommend-page { padding: $spacing-lg; background: $bg-page; min-height: calc(100vh - $top-nav-height); }
.page-header {
  margin-bottom: $spacing-lg;
  .page-title { font-size: 24px; font-weight: 700; color: $text-primary; margin-bottom: $spacing-xs; }
  .page-desc { font-size: 14px; color: $text-secondary; }
}

/* 流动小说名河流 */
.novel-river {
  position: relative; overflow: hidden; border-radius: 16px;
  background: linear-gradient(135deg, #1a1c2e 0%, #2d3561 40%, #1e3a5f 70%, #0d2137 100%);
  padding: 24px 0; margin-bottom: $spacing-lg;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);

  &::before {
    content: ''; position: absolute; inset: 0; pointer-events: none;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(102, 126, 234, 0.15) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 30%, rgba(118, 75, 162, 0.12) 0%, transparent 50%);
  }
}

.river-lane {
  display: flex; gap: 20px; white-space: nowrap;
  padding: 6px 0; animation: riverFlow linear infinite;
}

.river-name {
  display: inline-block; padding: 6px 18px; margin: 0 4px;
  border-radius: 20px; color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.06); backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  font-weight: 500; letter-spacing: 0.5px;
  transition: all 0.3s ease;
  &:hover { background: rgba(255, 255, 255, 0.15); color: #fff; transform: scale(1.05); }
}

@keyframes riverFlow {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}

/* 分类选择器 */
.category-selector {
  margin-bottom: $spacing-lg; background: $bg-white; padding: $spacing-md $spacing-lg;
  border-radius: $border-radius-lg; box-shadow: $box-shadow-light;
  :deep(.el-radio-button__inner) { border-radius: $border-radius-md !important; border: none; padding: 10px 28px; font-weight: 500; }
  :deep(.el-radio-group) { flex-wrap: wrap; gap: $spacing-sm; }
}

/* 河流图 */
.card-box {
  background: $bg-white; border-radius: $border-radius-lg; box-shadow: $box-shadow-light;
  padding: $spacing-lg; margin-bottom: $spacing-lg;
}
.card-title {
  font-size: 16px; font-weight: 600; color: $text-primary;
  padding-left: $spacing-sm; border-left: 3px solid $primary-color; margin-bottom: $spacing-md;
}
.river-chart { width: 100%; height: 320px; }

/* 小说卡片 */
.novel-grid { .el-col { margin-bottom: 20px; } }

.novel-card {
  background: $bg-white; border-radius: 14px; padding: 16px;
  box-shadow: $box-shadow-light; transition: transform 0.3s, box-shadow 0.3s; cursor: pointer;
  &:hover { transform: translateY(-4px); box-shadow: 0 12px 28px rgba(0, 0, 0, 0.1); }
}

.card-top-bar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 12px;
  .card-avatar {
    width: 48px; height: 48px; border-radius: 12px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; font-weight: 800; color: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  .card-info { flex: 1; min-width: 0; }
  .card-name {
    font-size: 15px; font-weight: 600; color: $text-primary;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .card-author { font-size: 12px; color: $text-secondary; margin-top: 2px; }
  .card-score {
    flex-shrink: 0; background: linear-gradient(135deg, #ff9a44, #fc6076);
    color: #fff; font-size: 14px; font-weight: 700;
    padding: 4px 10px; border-radius: 10px; min-width: 36px; text-align: center;
  }
}

.card-bottom {
  .card-meta {
    font-size: 12px; color: $primary-color; background: rgba(64, 158, 255, 0.06);
    padding: 6px 10px; border-radius: 8px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 4px;
  }
  .card-tags { display: flex; flex-wrap: wrap; gap: 4px; .el-tag { font-size: 11px; } }
}
</style>

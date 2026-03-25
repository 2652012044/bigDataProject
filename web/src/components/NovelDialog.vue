<template>
  <el-dialog v-model="show" :title="novel.bookName || '书籍详情'" width="720px" destroy-on-close class="novel-dialog">
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">{{ novel.bookName }}</span>
        <el-tag size="small" effect="light">{{ novel.category || '其他' }}</el-tag>
      </div>
    </template>

    <div class="novel-detail" style="position: relative;">
      <DanmakuLayer v-if="show" />

      <div class="detail-top">
        <div class="detail-cover" :style="{ background: coverGradient }">
          <img v-if="novel.thumbUrl" :src="novel.thumbUrl" class="cover-img" />
        </div>
        <div class="detail-info">
          <p><strong>作者：</strong>{{ novel.author }}</p>
          <p><strong>类型：</strong>{{ novel.category }}</p>
          <p><strong>字数：</strong>{{ novel.wordNumber ? (novel.wordNumber / 10000).toFixed(1) + '万字' : '未知' }}</p>
          <p><strong>状态：</strong><el-tag size="small" :type="novel.creationStatus === 1 ? 'info' : 'success'">{{ novel.creationStatus === 1 ? '已完结' : '连载中' }}</el-tag></p>
          <p><strong>评分：</strong><el-rate :model-value="(novel.score || 0) / 2" disabled show-score :score-template="`${novel.score || 0}`" size="small" /></p>
          <p class="desc"><strong>简介：</strong>{{ novel.bookAbstract || '暂无简介' }}</p>
        </div>
      </div>

      <el-tabs v-model="activeTab" class="detail-tabs">
        <el-tab-pane label="读者评论" name="comments">
          <!-- 评论情感统计条 -->
          <div v-if="sentimentSummary.totalComments > 0" class="sentiment-summary-bar">
            <div class="summary-progress">
              <div class="progress-segment positive-seg" :style="{ width: sentimentSummary.positiveRate + '%' }"></div>
              <div class="progress-segment neutral-seg" :style="{ width: (100 - sentimentSummary.positiveRate - negativeRate) + '%' }"></div>
              <div class="progress-segment negative-seg" :style="{ width: negativeRate + '%' }"></div>
            </div>
            <div class="summary-labels">
              <span class="label-positive">正面 {{ sentimentSummary.positive }}</span>
              <span class="label-neutral">中性 {{ sentimentSummary.neutral }}</span>
              <span class="label-negative">负面 {{ sentimentSummary.negative }}</span>
              <span class="label-total">共 {{ sentimentSummary.totalComments }} 条</span>
            </div>
          </div>

          <div v-if="comments.length === 0" style="text-align: center; color: #909399; padding: 20px;">暂无评论数据</div>
          <div class="comment-list">
            <div v-for="c in comments" :key="c.commentId" class="comment-item">
              <div class="comment-avatar-wrap" :class="'avatar-' + (c.sentimentLabel || 'neutral')">
                {{ (c.userName || '匿').charAt(0) }}
              </div>
              <div class="comment-body">
                <div class="comment-header">
                  <span class="comment-user">{{ c.userName || '匿名用户' }}</span>
                  <span class="comment-time" v-if="c.time">{{ c.time }}</span>
                  <span class="comment-digg" v-if="c.diggCount">{{ c.diggCount }} 赞</span>
                </div>
                <p class="comment-text">{{ c.content }}</p>
              </div>
              <div class="comment-sentiment" v-if="c.sentimentLabel">
                <el-tag :type="getSentimentTagType(c.sentimentLabel)" effect="dark" size="small" round>
                  {{ c.sentimentText }}
                </el-tag>
                <span class="score-text">{{ Math.round((c.sentimentScore || 0) * 100) }}%</span>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="相关推荐" name="related">
          <el-row :gutter="12">
            <el-col :span="6" v-for="(r, index) in relatedBooks" :key="r.bookId">
              <div class="related-card">
                <div class="related-cover" :style="{ background: relatedGradients[index % relatedGradients.length] }">
                  <img v-if="r.thumbUrl" :src="r.thumbUrl" class="cover-img" />
                </div>
                <span class="related-name">{{ r.bookName }}</span>
                <span class="related-author">{{ r.author }}</span>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>
      </el-tabs>
    </div>

    <template #footer>
      <el-button @click="handleCollect" :type="collected ? 'warning' : 'default'">
        <el-icon><StarFilled v-if="collected" /><Star v-else /></el-icon>
        {{ collected ? '已收藏' : '收藏' }}
      </el-button>
      <el-button type="primary" @click="show = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { UserFilled, Star, StarFilled } from '@element-plus/icons-vue'
import DanmakuLayer from './DanmakuLayer.vue'
import request from '@/api/index'

const props = defineProps({
  visible: Boolean,
  novelId: [Number, String]
})

const emit = defineEmits(['update:visible', 'collect'])

const show = computed({
  get: () => props.visible,
  set: v => emit('update:visible', v)
})

const activeTab = ref('comments')
const collected = ref(false)

const novel = ref({})
const comments = ref([])
const relatedBooks = ref([])
const sentimentSummary = ref({ totalComments: 0, positive: 0, neutral: 0, negative: 0, positiveRate: 0 })

const negativeRate = computed(() => {
  const total = sentimentSummary.value.totalComments
  if (total <= 0) return 0
  return Math.round(sentimentSummary.value.negative * 100 / total)
})

const coverGradient = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
const relatedGradients = [
  'linear-gradient(135deg, #43e97b, #38f9d7)',
  'linear-gradient(135deg, #fa709a, #fee140)',
  'linear-gradient(135deg, #2196f3, #0d47a1)',
  'linear-gradient(135deg, #a18cd1, #fbc2eb)'
]

const getSentimentTagType = (label) => {
  if (label === 'positive') return 'success'
  if (label === 'negative') return 'danger'
  return 'info'
}

async function loadBookDetail(bookId) {
  if (!bookId) return
  try {
    const res = await request.get(`/book/${bookId}`)
    const data = res.data || {}
    novel.value = data.book || {}
    comments.value = data.comments || []
    relatedBooks.value = data.relatedBooks || []
    sentimentSummary.value = data.sentimentSummary || { totalComments: 0, positive: 0, neutral: 0, negative: 0, positiveRate: 0 }
  } catch (e) { /* keep empty */ }
}

watch(() => props.visible, (newVal) => {
  if (newVal && props.novelId) {
    loadBookDetail(props.novelId)
  }
})

function handleCollect() {
  collected.value = !collected.value
  emit('collect', { novelId: props.novelId, collected: collected.value })
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.dialog-header { display: flex; align-items: center; gap: $spacing-sm; .dialog-title { font-size: 18px; font-weight: 700; } }
.detail-top { display: flex; gap: $spacing-lg; margin-bottom: $spacing-lg; }
.detail-cover { width: 180px; height: 240px; border-radius: $border-radius-md; flex-shrink: 0; overflow: hidden; .cover-img { width: 100%; height: 100%; object-fit: cover; } }
.detail-info { flex: 1; p { margin: 0 0 $spacing-sm; font-size: 14px; color: $text-regular; } .desc { line-height: 1.7; color: $text-secondary; } }

/* 情感统计条 */
.sentiment-summary-bar {
  margin-bottom: 16px; padding: 12px 16px; background: #f8f9fb; border-radius: 8px;
  .summary-progress {
    display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin-bottom: 8px;
    .progress-segment { transition: width 0.5s ease; }
    .positive-seg { background: #67c23a; }
    .neutral-seg { background: #dcdfe6; }
    .negative-seg { background: #f56c6c; }
  }
  .summary-labels {
    display: flex; gap: 16px; font-size: 12px;
    .label-positive { color: #67c23a; font-weight: 600; }
    .label-neutral { color: #909399; }
    .label-negative { color: #f56c6c; font-weight: 600; }
    .label-total { margin-left: auto; color: $text-secondary; }
  }
}

.comment-list {
  max-height: 400px; overflow-y: auto;
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

  .comment-item { display: flex; gap: $spacing-md; padding: $spacing-md 0; border-bottom: 1px solid $border-light; }

  .comment-avatar-wrap {
    width: 36px; height: 36px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; font-weight: 700; color: #fff;
    &.avatar-positive { background: linear-gradient(135deg, #67c23a, #85ce61); }
    &.avatar-neutral { background: linear-gradient(135deg, #909399, #b1b3b8); }
    &.avatar-negative { background: linear-gradient(135deg, #f56c6c, #f89898); }
  }

  .comment-body { flex: 1; min-width: 0; }
  .comment-header {
    display: flex; align-items: center; gap: $spacing-sm; margin-bottom: $spacing-xs;
    .comment-user { font-weight: 600; font-size: 14px; }
    .comment-time { font-size: 12px; color: $text-secondary; }
    .comment-digg { font-size: 12px; color: #e6a23c; }
  }
  .comment-text { margin: $spacing-xs 0; font-size: 14px; color: $text-regular; line-height: 1.6; word-break: break-all; }

  .comment-sentiment {
    flex-shrink: 0; display: flex; flex-direction: column; align-items: center; gap: 4px;
    .score-text { font-size: 11px; color: $text-secondary; }
  }
}

.related-card {
  text-align: center; cursor: pointer;
  .related-cover { width: 100%; height: 120px; border-radius: $border-radius-sm; margin-bottom: $spacing-xs; overflow: hidden; .cover-img { width: 100%; height: 100%; object-fit: cover; } }
  .related-name { display: block; font-size: 13px; font-weight: 600; color: $text-primary; }
  .related-author { font-size: 12px; color: $text-secondary; }
}
</style>

<template>
  <div class="novel-card" @click="handleClick">
    <div class="novel-card__cover" :style="{ background: coverGradient }">
      <div class="novel-card__cover-overlay">
        <span class="novel-card__cover-title">{{ novel.title }}</span>
      </div>
    </div>

    <div class="novel-card__info">
      <div class="novel-card__author text-ellipsis">{{ novel.author }}</div>

      <div class="novel-card__score">
        <el-rate
          :model-value="novel.score"
          disabled
          show-score
          score-template="{value}分"
          size="small"
        />
      </div>

      <div class="novel-card__meta">
        <el-tag size="small" :type="tagType" effect="light">{{ novel.type }}</el-tag>
      </div>
    </div>

    <div class="novel-card__actions">
      <el-button
        :type="isCollected ? 'warning' : 'default'"
        size="small"
        round
        @click.stop="handleCollect"
      >
        <el-icon>
          <StarFilled v-if="isCollected" />
          <Star v-else />
        </el-icon>
        <span>{{ isCollected ? '已收藏' : '收藏' }}</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Star, StarFilled } from '@element-plus/icons-vue'

const props = defineProps({
  novel: {
    type: Object,
    required: true,
    default: () => ({
      id: 0,
      title: '',
      author: '',
      cover: '',
      score: 0,
      type: '',
      collectDate: '',
    }),
  },
})

const emit = defineEmits(['click', 'collect'])

const isCollected = ref(!!props.novel.collectDate)

// Cover gradient based on novel type
const typeGradientMap = {
  '玄幻': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  '都市': 'linear-gradient(135deg, #2196f3 0%, #0d47a1 100%)',
  '仙侠': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  '科幻': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  '言情': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  '历史': 'linear-gradient(135deg, #c79081 0%, #dfa579 100%)',
  '悬疑': 'linear-gradient(135deg, #434343 0%, #000000 100%)',
  '军事': 'linear-gradient(135deg, #4b6cb7 0%, #182848 100%)',
  '游戏': 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
  '体育': 'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',
}

const coverGradient = computed(() => {
  return (
    typeGradientMap[props.novel.type] ||
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  )
})

// Tag type mapping
const typeTagMap = {
  '玄幻': '',
  '都市': 'success',
  '仙侠': 'warning',
  '科幻': 'danger',
  '言情': '',
  '历史': 'info',
  '悬疑': 'info',
}

const tagType = computed(() => {
  return typeTagMap[props.novel.type] || ''
})

function handleClick() {
  emit('click', props.novel)
}

function handleCollect() {
  isCollected.value = !isCollected.value
  emit('collect', { novel: props.novel, collected: isCollected.value })
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.novel-card {
  width: 220px;
  background: $bg-white;
  border-radius: $border-radius-md;
  box-shadow: $box-shadow-light;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  &__cover {
    width: 100%;
    height: 160px;
    position: relative;
    display: flex;
    align-items: flex-end;
  }

  &__cover-overlay {
    width: 100%;
    padding: $spacing-sm $spacing-md;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
  }

  &__cover-title {
    color: #fff;
    font-size: 15px;
    font-weight: 600;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
    line-height: 1.4;
  }

  &__info {
    padding: $spacing-sm $spacing-md;
  }

  &__author {
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: $spacing-xs;
  }

  &__score {
    margin-bottom: $spacing-xs;

    :deep(.el-rate) {
      height: 20px;

      .el-rate__icon {
        font-size: 14px;
      }

      .el-rate__text {
        font-size: 12px;
        color: $text-secondary;
      }
    }
  }

  &__meta {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
  }

  &__actions {
    padding: $spacing-xs $spacing-md $spacing-sm;
    display: flex;
    justify-content: center;

    .el-button {
      width: 100%;

      .el-icon {
        margin-right: 4px;
      }
    }
  }
}
</style>

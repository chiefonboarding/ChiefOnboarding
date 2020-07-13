<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="950"
  >
    <v-card>
      <v-card-title class="headline mx-2">
        {{ $t('sequence.badgeModal') }}
      </v-card-title>

      <v-card-text>
        <BadgeForm v-model="tempBadge" :errors="errors" :inline="true" class="form" />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          @click="$emit('input', false)"
          text
        >
          {{ $t('buttons.cancel') }}
        </v-btn>
        <v-btn
          :loading="loading"
          @click="addBadge"
        >
          <span v-if="Object.entries(badge).length">
            {{ $t('buttons.update') }}
          </span>
          <span v-else>
            {{ $t('buttons.add') }}
          </span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import BadgeForm from '@/components/admin/badge/Form'
export default {
  name: 'BadgeModal',
  components: { BadgeForm },
  props: {
    badge: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    },
    value: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    loading: false,
    errors: {},
    tempBadge: { name: '', content: [], tags: [] }
  }),
  watch: {
    value (value) {
      if (Object.entries(this.badge).length === 0) {
        this.tempBadge = { name: '', content: [], tags: [], image: null }
      } else {
        this.tempBadge = JSON.parse(JSON.stringify(this.badge))
      }
    }
  },
  methods: {
    addBadge () {
      this.tempBadge.template = false
      this.loading = true
      this.$badges.create(this.tempBadge).then((data) => {
        if ('id' in this.badge) {
          this.$store.commit('sequences/removeItem', {
            block: this.index,
            type: 'badges',
            id: this.badge.id
          })
        }
        this.$store.commit('sequences/addItem', { block: this.index, type: 'badges', item: data })
        this.$emit('input', false)
      }).catch((error) => {
        this.errors = error
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>

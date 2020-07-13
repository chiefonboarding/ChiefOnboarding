<template>
  <v-container style="max-width: 600px;">
    <v-timeline dense clipped>
      <v-timeline-item
        v-if="!fullReadOnly"
        fill-dot
        class="white--text mb-5"
        color="orange"
        large
      >
        <span slot="icon">{{ $t('newhires.you') }}</span>
        <v-text-field
          v-model="comment"
          :label="$t('hrTask.leaveComment')"
          @keydown.enter="makeComment"
          hide-details
          text
          solo
        >
          <template slot="append">
            <v-btn
              :loading="loading"
              @click="makeComment"
              class="mx-0"
              depressed
            >
              {{ $t('buttons.post') }}
            </v-btn>
          </template>
        </v-text-field>
      </v-timeline-item>

      <v-timeline-item
        v-for="i in value.comments"
        :key="i.id"
        class="mb-3"
        color="grey"
        small
      >
        <v-row justify-space-between>
          <v-col xs="7" style="vertical-align:middle">
            {{ i.content }}
            <div class="caption">
              - {{ i.comment_by.full_name }}
            </div>
          </v-col>
          <v-col xs="5" class="text-right">
            {{ i.date | timeAgo }}
          </v-col>
        </v-row>
      </v-timeline-item>
    </v-timeline>
  </v-container>
</template>

<script>
export default {
  props: {
    'value': {
      type: Object,
      required: true
    },
    'errors': {
      type: Object,
      required: true
    },
    'fullReadOnly': {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    input: '',
    loading: false,
    comment: ''
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  },
  mounted () {
  },
  methods: {
    makeComment () {
      this.loading = true
      this.$hrtasks.addComment(this.$route.params.id, { 'content': this.comment }).then((response) => {
        this.$emit('value', this.value.comments.unshift(response))
        this.comment = ''
        this.$store.dispatch('showSnackbar', this.$t('hrTask.addedComment'))
      }).catch((error) => {
        this.$store.dispatch('showSnackbar', this.$t('hrTask.couldNotBeAdded'))
      }).finally(() => {
        this.loading = false
      })
    }
  }
}
</script>

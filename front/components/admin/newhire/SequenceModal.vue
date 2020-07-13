<template>
  <v-dialog
    v-model="value"
    :persistent="true"
    max-width="650"
  >
    <v-card>
      <v-card-title class="headline">
        {{ $t('sequence.addRightAway') }}
      </v-card-title>

      <v-card-text>
        <v-row v-for="(i, index) in items" :key="index" mt-3>
          <v-col sm="1">
            <v-checkbox
              :input-value="i.check"
              v-model="i.check"
            />
          </v-col>
          <v-divider vertical />
          <v-col sm="11" mx-4>
            <v-chip v-if="hasNewHireItems(i)" label small style="margin: 5px 0px;">
              {{ $t('sequence.addToNewHire') }}
            </v-chip>
            <CardLine :index="index" :removable="false" :items="i.todo" type="todo" />
            <CardLine :index="index" :removable="false" :items="i.book" type="book" />
            <CardLine :index="index" :removable="false" :items="i.badge" type="badge" />
            <CardLine :index="index" :removable="false" :items="i.slack" type="slack" />
            <CardLine :index="index" :removable="false" :items="i.text" type="text" />
            <CardLine :index="index" :removable="false" :items="i.email" type="email" />

            <v-chip v-if="hasAdminItems(i)" label small style="margin: 5px 0px;">
              {{ $t('sequence.addToAdmin') }}
            </v-chip>
            <CardLine :index="index" :removable="false" :items="i.task" type="task" />
            <CardLine :index="index" :removable="false" :items="i.text_admin" type="text_admin" />
            <CardLine :index="index" :removable="false" :items="i.email_admin" type="email_admin" />
            <CardLine :index="index" :removable="false" :items="i.slack_admin" type="slack_admin" />
          </v-col>
        </v-row>
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
          @click="triggerSequenceItem"
        >
          <span>
            {{ $t('buttons.add') }}
          </span>
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import CardLine from '@/components/admin/sequence/CardLine'
export default {
  name: 'SequenceModal',
  components: { CardLine },
  props: {
    items: {
      type: Array,
      default: () => { return [] }
    },
    value: {
      type: Boolean,
      default: false
    },
    id: {
      type: Number,
      default: 0
    }
  },
  data () {
    return {
      loading: false
    }
  },
  methods: {
    triggerSequenceItem () {
      const triggers = []
      this.items.forEach((item) => {
        if (item.check) { triggers.push(item.id) }
      })
      this.loading = true
      this.$newhires.triggerItems(this.$route.params.id || this.id, { triggers }).then(() => {
        this.$emit('input', false)
      }).finally(() => {
        this.loading = false
      })
    },
    hasNewHireItems (i) {
      return i.todo.length || i.book.length || i.badge.length || i.text.length || i.slack.length || i.email.length
    },
    hasAdminItems (i) {
      return i.task.length || i.text_admin.length || i.slack_admin.length || i.email_admin.length
    }
  }
}
</script>

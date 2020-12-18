<template>
  <v-container class="py-2 px-0">
    <v-row>
      <v-col sm="4">
        <v-col sm="12" class="py-0">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('forms.title')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col sm="12" class="py-0">
          <v-text-field
            v-model="value.due_on_day"
            :label="$t('resource.dueOnWorkday')"
            :error-messages="errorMessages.due_on_day"
            @keyup="errorMessages.due_on_day=''"
            type="number"
          />
        </v-col>
        <v-col sm="12" class="py-0">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
      </v-col>
      <v-col sm="8" class="pl-4">
        <Editor ref="editor" v-model="value.content" />
        <CustomForm v-if="'form' in value" v-model="value.form" add-integrations />
        <v-col v-if="$store.state.org.slack_key && 'form' in value && value.form.length" sm="12">
          <v-checkbox
            v-model="value.send_back"
            :label="$t('todo.sendFormBack')"
          />
          <div v-if="value.send_back">
            <v-combobox
              v-model="value.channel"
              :items="$store.state.slackChannels"
              :label="$t('todo.selectSlackChannel')"
              :hint="$t('todo.botInvited')"
              :persistent-hint="true"
            />
          </div>
        </v-col>
      </v-col>
    </v-row>
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
    'inline': {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    search: ''
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    }
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    }
  }
}
</script>

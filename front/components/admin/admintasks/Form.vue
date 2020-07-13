<template>
  <div style="width: 100%">
    <v-col sm="12" class="py-0">
      <v-text-field
        v-model="value.name"
        :label="$t('forms.name')"
        :disabled="fullReadOnly"
        :error-messages="errorMessages.name"
        @keyup="errorMessages.name=''"
      />
    </v-col>
    <v-col v-if="!noNewHire" sm="12" class="py-0">
      <v-autocomplete
        v-model="value.new_hire"
        :items="$store.state.newhires.all"
        :disabled="newHireReadOnly || fullReadOnly"
        :label="$t('hrTask.newHire')"
        item-value="email"
        return-object
        item-text="full_name"
      />
    </v-col>
    <v-col sm="12" class="py-0">
      <v-autocomplete
        v-model="value.assigned_to"
        :items="$store.state.admins"
        :label="$t('hrTask.assignedTo')"
        :disabled="fullReadOnly"
        return-object
        item-value="email"
        item-text="full_name"
      />
    </v-col>
    <v-col sm="12" class="py-0">
      <v-menu
        v-model="menu1"
        :disabled="fullReadOnly"
        :close-on-content-click="false"
        max-width="290"
      >
        <template v-slot:activator="{ on }">
          <v-text-field
            v-model="computedDateFormattedMomentjs"
            :disabled="fullReadOnly"
            :label="$t('hrTask.due')"
            :error-messages="errorMessages.date"
            v-on="on"
            @keyup="errorMessages.date=''"
            readonly
            prepend-icon="event"
          />
        </template>
        <v-date-picker
          v-model="value.date"
          :locale="$store.state.org.locale"
          :disabled="fullReadOnly"
          @change="menu1 = false"
        />
      </v-menu>
    </v-col>
    <v-col sm="12" class="py-0">
      <v-select
        v-model="value.priority"
        :items="states"
        :label="$t('hrTask.priority')"
        :disabled="fullReadOnly"
        hide-details
        prepend-icon="far fa-flag"
        item-text="name"
        item-value="id"
      />
    </v-col>
    <v-col v-if="showLastField" sm="12" style="margin-top: 10px;">
      <VTextAreaEmoji
        v-model="value.comment"
        :label="$t('hrTask.moreDetails')"
        :personalize="personalize"
        :emoji="true"
        :disabled="fullReadOnly"
      />
    </v-col>
    <v-col v-if="showLastField" class="py-0" sm="12">
      <v-select
        v-model="value.option"
        :items="[{text: $t('hrTask.doNotNotify'), option: '0'}, {text: $t('hrTask.sendEmail'), option: '1'}, {text: $t('hrTask.sendSlack'), option: '2'}]"
        :label="$t('hrTask.notify')"
        :disabled="fullReadOnly"
        hide-details
        item-text="text"
        item-value="option"
      />
    </v-col>
    <v-col v-if="showLastField && value.option === '1'" sm="12" class="py-0" style="margin-top: 10px;">
      <v-text-field
        v-model="value.email"
        :label="$t('hrTask.email')"
        type="email"
      />
    </v-col>
    <v-col v-if="showLastField && value.option === '2'" sm="12" class="py-0" style="margin-top: 10px;">
      <v-autocomplete
        v-model="value.slack"
        :items="pickSomeone"
        :label="$t('hrTask.pick')"
      />
    </v-col>
  </div>
</template>

<script>
import moment from 'moment'
export default {
  name: 'AdminTaskForm',
  props: {
    'value': {
      type: Object,
      required: true
    },
    'errors': {
      type: Object,
      required: true
    },
    'newHireReadOnly': {
      type: Boolean,
      default: false
    },
    'personalize': {
      type: Boolean,
      default: false
    },
    'noNewHire': {
      type: Boolean,
      default: false
    },
    'showLastField': {
      type: Boolean,
      default: true
    },
    'fullReadOnly': {
      type: Boolean,
      default: false
    }
  },
  data: vm => ({
    menu1: false,
    states: [
      { name: vm.$t('hrTask.low'), id: 1 },
      { name: vm.$t('hrTask.medium'), id: 2 },
      { name: vm.$t('hrTask.high'), id: 3 }
    ]
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    },
    pickSomeone () {
      return this.$store.state.slackPeople.map(one => one.name + ' (' + one.id + ')')
    },
    computedDateFormattedMomentjs () {
      let date = ''
      if (this.value.date) {
        date = moment(this.value.date)
      } else {
        return date
      }
      if (this.$store.state.org.user_language === 'nl') {
        return date.format('dddd, D MMMM YYYY')
      } else {
        return date.format('dddd, MMMM Do YYYY')
      }
    }
  },
  watch: {
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
    },
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    'value.slack' (value) {
      this.value.email_slack = value
    },
    'value.email' (value) {
      this.value.email_slack = value
    },
    'value.assigned_to' (value) {
      this.value.assigned_to_id = value.id
    },
    'value.new_hire' (value) {
      this.value.new_hire_id = value.id
    }
  }
}
</script>

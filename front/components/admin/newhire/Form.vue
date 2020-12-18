<template>
  <div style="width: 100%;">
    <v-container class="pa-0">
      <v-row>
        <v-col cols="6" class="py-0">
          <v-text-field
            ref="firstName"
            v-model="value.first_name"
            :label="$t('forms.firstName')"
            :error-messages="errorMessages.first_name"
            @keyup="errorMessages.first_name=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-text-field
            v-model="value.last_name"
            :label="$t('forms.lastName')"
            :error-messages="errorMessages.last_name"
            @keyup="errorMessages.last_name=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-text-field
            v-model="value.email"
            :label="$t('forms.email')"
            :error-messages="errorMessages.email"
            @keyup="errorMessages.email=''"
            hint="Business email address"
            persistent-hint
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-text-field
            v-model="value.personal_meail"
            :label="$t('forms.email')"
            :error-messages="errorMessages.email"
            @keyup="errorMessages.email=''"
            hint="Personal email address"
            persistent-hint
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-text-field
            v-model="value.phone"
            :label="$t('forms.phone')"
            :error-messages="errorMessages.phone"
            @keyup="errorMessages.phone=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-text-field
            v-model="value.position"
            :label="$t('forms.position')"
            :error-messages="errorMessages.position"
            @keyup="errorMessages.position=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-menu
            v-if="!disabled"
            v-model="showPicker"
            :close-on-content-click="false"
            :nudge-right="40"
            transition="scale-transition"
            offset-y
            min-width="290px"
          >
            <template v-slot:activator="{ on }">
              <v-text-field
                v-model="computedDateFormattedMomentjs"
                :label="$t('forms.startDate')"
                v-on="on"
                prepend-icon="event"
                readonly
              />
            </template>
            <v-date-picker
              v-model="value.start_day"
              :first-day-of-week="1"
              :error-messages="errorMessages.start_day"
              :locale="$store.state.org.locale"
              :allowed-dates="allowedDates"
              @input="showPicker = false"
              @change="errorMessages.start_day=''"
            />
          </v-menu>
        </v-col>
        <v-col cols="6" class="py-0" />
        <v-col v-if="$store.state.org.slack_key" cols="12" class="py-0">
          <v-textarea
            v-model="value.message"
            :label="$t('forms.shareNewHire')"
            :hint="$t('forms.shareNewHireHint')"
            :error-messages="errorMessages.message"
            @keyup="errorMessages.message=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-autocomplete
            v-model="value.timezone"
            :items="$store.state.timezones"
            :search-input.sync="search"
            :label="$t('forms.newHireTimezone')"
            :error-messages="errorMessages.timezone"
            @keyup="errorMessages.timezone=''"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-autocomplete
            v-model="value.language"
            :items="$store.state.languages"
            :label="$t('forms.newHireLanguage')"
            :error-messages="errorMessages.language"
            @keyup="errorMessages.language=''"
            item-text="language"
            item-value="id"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-autocomplete
            v-model="value.buddy"
            :items="$store.state.employees.all"
            :label="$t('forms.newHiresBuddy')"
            item-text="full_name"
            item-value="id"
          />
        </v-col>
        <v-col cols="6" class="py-0">
          <v-autocomplete
            v-model="value.manager"
            :items="$store.state.employees.all"
            :label="$t('forms.newHiresManager')"
            item-text="full_name"
            item-value="id"
          />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import moment from 'moment'
export default {
  props: {
    value: {
      type: Object,
      default: () => { return {} }
    },
    errors: {
      type: Object,
      default: () => { return {} }
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  data: () => ({
    start: '',
    search: '',
    showPicker: false
  }),
  computed: {
    errorMessages () {
      if ('start' in this.errors) {
        this.$store.commit('setSnackbar', this.errors.start_day)
      }
      return JSON.parse(JSON.stringify(this.errors))
    },
    computedDateFormattedMomentjs () {
      let date = moment()
      if (this.value.start_day) {
        date = moment(this.value.start_day)
      }
      if (this.$store.state.admin.language === 'nl') {
        return date.format('dddd, D MMMM YYYY')
      } else {
        return date.format('dddd, MMMM Do YYYY')
      }
    }
  },
  watch: {
    value: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    }
  },
  mounted () {
    this.$employees.getAll()
  },
  methods: {
    allowedDates: val => ![0, 6].includes(moment.utc(val).day())
  }
}
</script>

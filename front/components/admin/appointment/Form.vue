<template>
  <v-container grid-list-md pa-4>
    <v-row>
      <v-col sm="4">
        <v-col sm="12" class="py-0">
          <VTextFieldEmoji
            v-model="value.name"
            :label="$t('forms.name')"
            :errors="errorMessages.name"
            @removeError="errorMessages.name=''"
          />
        </v-col>
        <v-col sm="12" class="py-0">
          <TagsSelector v-model="value.tags" class="pt-2" />
        </v-col>
        <v-col sm="12" class="py-0">
          <v-switch
            v-model="value.fixed_date"
            :label="$t('forms.fixedDate')"
            style="margin-top: 0px;"
          />
        </v-col>
        <v-col v-if="value.fixed_date" sm="12" class="py-0">
          <v-menu
            v-model="showPicker"
            :close-on-content-click="false"
            :nudge-right="40"
            lazy
            transition="scale-transition"
            offset-y
            full-width
            min-width="290px"
          >
            <template v-slot:activator="{ on }">
              <v-text-field
                v-model="computedDateFormattedMomentjs"
                :label="$t('forms.appointmentDate')"
                v-on="on"
                prepend-icon="event"
              />
            </template>
            <v-date-picker
              v-model="value.date"
              :first-day-of-week="1"
              :error-messages="errorMessages.date"
              :locale="$store.state.org.locale"
              @input="showPicker = false"
              @change="errorMessages.date=''"
            />
          </v-menu>
        </v-col>
        <v-col v-else sm="12" class="py-0">
          <v-text-field
            v-model="value.on_day"
            :label="$t('forms.workDay')"
            :error-messages="errorMessages.on_day"
            :hint="$t('forms.workDayHint')"
            @keyup="errorMessages.on_day=''"
            type="number"
          />
        </v-col>
        <v-col sm="12" class="py-0">
          <v-menu
            ref="menu"
            v-model="menu2"
            :close-on-content-click="false"
            :nudge-right="40"
            lazy
            transition="scale-transition"
            offset-y
            full-width
            max-width="290px"
            min-width="290px"
            class="mt-2"
          >
            <template v-slot:activator="{ on }">
              <v-text-field
                v-model="value.time"
                :label="$t('forms.chooseTime')"
                :error-messages="errorMessages.time"
                @change="errorMessages.time=''"
                v-on="on"
                prepend-icon="access_time"
                readonly
              />
            </template>
            <v-time-picker
              v-if="menu2"
              v-model="time"
              @change="$refs.menu.save(time)"
              full-width
            />
          </v-menu>
        </v-col>
      </v-col>
      <v-col sm="8" class="py-0">
        <Editor ref="editor" v-model="value.content" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import moment from 'moment'
export default {
  props: {
    value: {
      type: Object,
      required: true
    },
    errors: {
      type: Object,
      required: true
    }
  },
  data: () => ({
    search: '',
    menu2: false,
    time: null,
    showPicker: false
  }),
  computed: {
    errorMessages () {
      return JSON.parse(JSON.stringify(this.errors))
    },
    computedDateFormattedMomentjs () {
      let date = moment()
      if (this.value.date) {
        date = moment(this.value.date)
      }
      if (this.$store.state.org.user_language === 'nl') {
        return date.format('dddd, D MMMM YYYY')
      } else {
        return date.format('dddd, MMMM Do YYYY')
      }
    }
  },
  watch: {
    appointment: {
      handler (value) {
        this.$emit('input', value)
      },
      deep: true
    },
    errors (value) {
      if ('content' in value) {
        this.$store.dispatch('showSnackbar', 'Content: ' + value.content[0])
      }
      if ('date' in value) {
        this.$store.dispatch('showSnackbar', 'Date: ' + value.date[0])
      }
    },
    time (value) {
      this.value.time = value
    }
  }
}
</script>

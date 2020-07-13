<template>
  <v-row style="max-width: 100%">
    <v-col cols="6" class="py-0">
      <v-text-field
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
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.email"
        :label="$t('forms.email')"
        :error-messages="errorMessages.email"
        @keyup="errorMessages.email=''"
        type="email"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.position"
        :label="$t('forms.position')"
        :error-messages="errorMessages.position"
        @keyup="errorMessages.position=''"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.phone"
        :label="$t('forms.phone')"
        :error-messages="errorMessages.phone"
        @keyup="errorMessages.phone=''"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.twitter"
        :error-messages="errorMessages.twitter"
        @keyup="errorMessages.twitter=''"
        label="Twitter"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.facebook"
        :error-messages="errorMessages.facebook"
        @keyup="errorMessages.facebook=''"
        label="Facebook"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-text-field
        v-model="value.linkedin"
        :error-messages="errorMessages.linkedin"
        @keyup="errorMessages.linkedin=''"
        label="Linkedin"
      />
    </v-col>
    <v-col cols="12" class="py-0">
      <v-textarea
        v-model="value.message"
        :label="$t('forms.message')"
        :hint="$t('forms.messageHint')"
        :persistent-hint="true"
        :error-messages="errorMessages.message"
        @keyup="errorMessages.message=''"
      />
    </v-col>
    <v-col cols="12" class="py-0 mt-2">
      <label>{{ $t('forms.profilePicture') }}</label>
      <v-file v-model="value.profile_image" style="width:100%" />
    </v-col>
  </v-row>
</template>

<script>
export default {
  props: {
    value: {
      type: Object,
      default: () => {
        return {}
      }
    },
    errors: {
      type: Object,
      default: () => {
        return {}
      }
    }
  },
  data: () => ({
    employee: '',
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
    'value.profile_image' (value) {
      this.value.profile_image_id = value.id
    }
  }
}
</script>

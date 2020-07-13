<template>
  <v-row wrap>
    <v-col sm="12" mb="6" offset-mb="3" md="6" offset-sm="3">
      <v-row mb-4>
        <v-col sm="6">
          <h1 class="heading" style="margin-top: 5px;">
            {{ $t('settings.personal.personal') }}
          </h1>
        </v-col>
      </v-row>
      <ResetPasswordForm />
      <ChangeLanguage />
    </v-col>
  </v-row>
</template>

<script>
import ResetPasswordForm from '@/components/admin/settings/ResetPasswordForm'
import ChangeLanguage from '@/components/admin/settings/ChangeLanguage'

export default {
  layout: 'admin',
  components: { ResetPasswordForm, ChangeLanguage }
}
</script>

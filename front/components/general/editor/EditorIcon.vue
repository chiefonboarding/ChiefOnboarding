<template>
  <div :class="[`icon--${name}`, `icon--${size}`, { 'has-align-fix': fixAlign }]" class="icon">
    <svg class="icon__svg">
      <use :xlink:href="'#icon--' + name" xmlns:xlink="http://www.w3.org/1999/xlink">
        <slot />
      </use>
    </svg>
  </div>
</template>

<script>
export default {
  props: {
    name: {
      type: String,
      default: ''
    },
    size: {
      default: 'normal',
      type: String
    },
    fixAlign: {
      default: true,
      type: Boolean
    }
  }
}
</script>

<style lang="scss" scoped>
.icon {
  position: relative;
  display: inline-block;
  vertical-align: middle;
  width: 0.8rem;
  height: 0.8rem;
  margin: 0 .3rem;
  top: -.05rem;
  fill: currentColor;
}
.icon__svg {
  display: inline-block;
  vertical-align: top;
  width: 100%;
  height: 100%;
}
.icon:first-child {
  margin-left: 0;
}
.icon:last-child {
  margin-right: 0;
}
.menubar__button {

}
</style>

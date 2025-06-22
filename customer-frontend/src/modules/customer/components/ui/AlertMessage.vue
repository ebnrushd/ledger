<template>
  <div v-if="visible && message" :class="alertClasses" role="alert">
    <div class="flex">
      <div class="py-1">
        <!-- Optional: Icon based on type -->
        <svg v-if="type === 'success'" class="fill-current h-6 w-6 text-green-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM6.7 9.29L9 11.6l4.3-4.3 1.4 1.42L9 14.4l-3.7-3.7 1.4-1.42z"/></svg>
        <svg v-if="type === 'error'" class="fill-current h-6 w-6 text-red-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm1.41-1.41A8 8 0 1 0 15.66 4.34 8 8 0 0 0 4.34 15.66zm9.9-8.49L11.41 10l2.83 2.83-1.41 1.41L10 11.41l-2.83 2.83-1.41-1.41L8.59 10 5.76 7.17l1.41-1.41L10 8.59l2.83-2.83 1.41 1.41z"/></svg>
        <svg v-if="type === 'info'" class="fill-current h-6 w-6 text-blue-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM9 11V9h2v6H9v-4zm0-6h2v2H9V5z"/></svg>
        <svg v-if="type === 'warning'" class="fill-current h-6 w-6 text-yellow-500 mr-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M2.93 17.07A10 10 0 1 1 17.07 2.93 10 10 0 0 1 2.93 17.07zm12.73-1.41A8 8 0 1 0 4.34 4.34a8 8 0 0 0 11.32 11.32zM9 5v6h2V5H9zm0 8h2v2H9v-2z"/></svg>
      </div>
      <div>
        <p class="font-bold">{{ title }}</p>
        <p class="text-sm">{{ message }}</p>
      </div>
    </div>
    <button v-if="dismissible" @click="dismiss" class="absolute top-0 bottom-0 right-0 px-4 py-3">
      <svg class="fill-current h-6 w-6" :class="closeButtonClasses" role="button" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>Close</title><path d="M14.348 14.849a1.2 1.2 0 0 1-1.697 0L10 11.819l-2.651 3.029a1.2 1.2 0 1 1-1.697-1.697l2.758-3.15-2.759-3.152a1.2 1.2 0 1 1 1.697-1.697L10 8.183l2.651-3.031a1.2 1.2 0 1 1 1.697 1.697l-2.758 3.152 2.758 3.15a1.2 1.2 0 0 1 0 1.698z"/></svg>
    </button>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref, PropType, watch } from 'vue';

type AlertType = 'success' | 'error' | 'info' | 'warning';

export default defineComponent({
  name: 'AlertMessage',
  props: {
    type: {
      type: String as PropType<AlertType>,
      default: 'info',
      validator: (value: string) => ['success', 'error', 'info', 'warning'].includes(value),
    },
    message: {
      type: String,
      required: true,
    },
    title: {
      type: String,
      default: '', // Default title can be set based on type if needed
    },
    dismissible: {
      type: Boolean,
      default: false,
    },
    show: { // Prop to control visibility externally
        type: Boolean,
        default: true
    }
  },
  emits: ['dismissed'],
  setup(props, { emit }) {
    const visible = ref(props.show);

    watch(() => props.show, (newValue) => {
        visible.value = newValue;
    });

    const alertClasses = computed(() => {
      const baseClasses = 'p-4 mb-4 border rounded-md relative';
      const typeClasses = {
        success: 'bg-green-100 border-green-400 text-green-700',
        error: 'bg-red-100 border-red-400 text-red-700',
        info: 'bg-blue-100 border-blue-400 text-blue-700',
        warning: 'bg-yellow-100 border-yellow-400 text-yellow-700',
      };
      return `${baseClasses} ${typeClasses[props.type]}`;
    });

    const closeButtonClasses = computed(() => {
        const typeClasses = {
            success: 'text-green-500 hover:text-green-700',
            error: 'text-red-500 hover:text-red-700',
            info: 'text-blue-500 hover:text-blue-700',
            warning: 'text-yellow-500 hover:text-yellow-700',
        };
        return typeClasses[props.type];
    });

    const computedTitle = computed(() => {
        if (props.title) return props.title;
        switch(props.type) {
            case 'success': return 'Success!';
            case 'error': return 'Error!';
            case 'info': return 'Information:';
            case 'warning': return 'Warning:';
            default: return 'Notice:';
        }
    });

    const dismiss = () => {
      visible.value = false;
      emit('dismissed');
    };

    return {
      alertClasses,
      closeButtonClasses,
      computedTitle,
      visible,
      dismiss,
    };
  },
});
</script>

<style scoped>
/* Scoped styles if needed, but Tailwind should cover most. */
pre { /* For displaying JSON in audit log example */
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
```

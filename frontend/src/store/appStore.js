import { create } from 'zustand'

export const useAppStore = create((set) => ({
  activeMessage: '',
  setActiveMessage: (msg) => set({ activeMessage: msg }),

  activeProfile: null,
  setActiveProfile: (profile) => set({ activeProfile: profile }),

  dwellTime: 1500,
  setDwellTime: (ms) => set({ dwellTime: ms }),

  isCalibrated: false,
  setCalibrated: (v) => set({ isCalibrated: v }),

  trackingEngine: 'mock',
  setTrackingEngine: (e) => set({ trackingEngine: e }),
}))

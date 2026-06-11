import { useState } from 'react'
import { useDwell } from '../hooks/useDwell'
import { DWELL_TIME_MS } from '../theme/lumina'

export default function GazeButton({
  children,
  onActivate,
  className = '',
  dwellTime = DWELL_TIME_MS,
  as: Tag = 'button',
  ...props
}) {
  const [hovered, setHovered] = useState(false)

  const { onMouseEnter, onMouseLeave } = useDwell(
    onActivate || (() => {}),
    dwellTime,
  )

  const handleEnter = () => {
    setHovered(true)
    onMouseEnter()
  }

  const handleLeave = () => {
    setHovered(false)
    onMouseLeave()
  }

  return (
    <Tag
      className={`glass-panel gaze-glow transition-all relative overflow-hidden ${className}`}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      {...props}
    >
      {children}
      {/* Barra de progresso dwell */}
      <div
        className={`dwell-bar ${hovered ? 'dwell-bar-active' : ''}`}
        style={{ '--dwell-ms': `${dwellTime}ms` }}
      />
    </Tag>
  )
}

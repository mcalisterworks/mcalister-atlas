import { useEffect, useRef } from 'react'
import {
  Viewer,
  ImageryLayer,
  ArcGisMapServerImageryProvider,
  Rectangle,
} from 'cesium'

import 'cesium/Build/Cesium/Widgets/widgets.css'
import './App.css'

function App() {
  const cesiumContainer = useRef(null)

  useEffect(() => {
    let viewer

    async function initializeCesium() {
      const imageryProvider =
        await ArcGisMapServerImageryProvider.fromUrl(
          'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer'
        )

      const imageryLayer = new ImageryLayer(imageryProvider)

      viewer = new Viewer(cesiumContainer.current, {
        baseLayer: imageryLayer,

        baseLayerPicker: false,
        animation: false,
        timeline: false,
        geocoder: false,
        homeButton: true,
        sceneModePicker: false,
        navigationHelpButton: false,
      })

      viewer.camera.setView({
        destination: Rectangle.fromDegrees(
          -95.0,
          25.0,
          -80.0,
          50.0
        ),
      })
    }

    initializeCesium()

    return () => {
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy()
      }
    }
  }, [])

  return <div ref={cesiumContainer} className="cesium-container" />
}

export default App

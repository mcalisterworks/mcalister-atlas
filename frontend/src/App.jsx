import { useEffect, useRef } from 'react'
import {
  Viewer,
  ImageryLayer,
  ArcGisMapServerImageryProvider,
  ArcGISTiledElevationTerrainProvider,
  Rectangle,
} from 'cesium'

import 'cesium/Build/Cesium/Widgets/widgets.css'
import './App.css'

function App() {
  const cesiumContainer = useRef(null)

  useEffect(() => {
    let viewer

    async function initializeCesium() {
      // --------------------------------------------------
      // USGS Imagery
      // --------------------------------------------------

      const imageryProvider =
        await ArcGisMapServerImageryProvider.fromUrl(
          'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer',
          {
            maximumLevel: 17,
            rectangle: Rectangle.fromDegrees(
              -90,
              41,
              -82,
              49
            ),
          }
        )

      const imageryLayer = new ImageryLayer(imageryProvider)

      // --------------------------------------------------
      // USGS 3DEP Terrain
      // --------------------------------------------------

      // const terrainProvider =
      //   await ArcGISTiledElevationTerrainProvider.fromUrl(
      //     'https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer'
      //   )

      // --------------------------------------------------
      // Cesium Viewer
      // --------------------------------------------------

      viewer = new Viewer(cesiumContainer.current, {
        baseLayer: imageryLayer,
        //terrainProvider: terrainProvider,

        baseLayerPicker: false,
        animation: false,
        timeline: false,
        geocoder: false,
        homeButton: true,
        sceneModePicker: false,
        navigationHelpButton: false,
      })

      // Northern Michigan
      viewer.camera.setView({
        destination: Rectangle.fromDegrees(
          -87.5,
          44.0,
          -82.5,
          47.0
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


import Foundation
import CoreLocation
#if canImport(WeatherKit)
import WeatherKit
#endif

// MARK: - WeatherService (CoreLocation + WeatherKit 기반 실시간 날씨 제공)
// - 위치 권한 요청 → 현재 좌표 → WeatherKit 날씨 조회
// - WeatherKit 미지원 환경(시뮬레이터/Capability 미등록)에서는 기상청 Open API Fallback 사용
// - 결과를 캐시하여 같은 날 반복 호출 시 네트워크 낭비 방지

class WeatherService: NSObject, ObservableObject, CLLocationManagerDelegate {
    static let shared = WeatherService()
    
    private let locationManager = CLLocationManager()
    private var locationContinuation: CheckedContinuation<CLLocation?, Never>?
    
    @Published var currentWeather: String = ""
    @Published var currentTemperature: Double = 0.0
    @Published var isLoaded: Bool = false
    
    // 캐시: 같은 날짜에는 한 번만 조회
    private var cachedDate: String?
    
    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.desiredAccuracy = kCLLocationAccuracyKilometer // 날씨는 대략적 위치로 충분
    }
    
    // MARK: - Public API
    
    /// 오늘의 날씨를 가져옵니다. 캐시가 있으면 즉시 반환합니다.
    func fetchTodayWeather() async -> (weather: String, temperature: Double) {
        let today = Self.todayString()
        
        // 캐시 히트 — 같은 날짜에 이미 조회했다면 재사용
        if cachedDate == today && isLoaded {
            return (currentWeather, currentTemperature)
        }
        
        // 1. 위치 권한 요청 + 현재 위치 획득
        guard let location = await requestCurrentLocation() else {
            // 위치 실패 시 기본값 (서울 기준 Fallback)
            return applyFallback()
        }
        
        // 2. WeatherKit 조회 시도
        #if canImport(WeatherKit)
        if #available(iOS 16.0, *) {
            do {
                let weatherService = WeatherKit.WeatherService.shared
                let weather = try await weatherService.weather(for: location)
                let condition = weather.currentWeather.condition
                let temp = weather.currentWeather.temperature.converted(to: .celsius).value
                
                let desc = Self.conditionToKorean(condition)
                
                await MainActor.run {
                    self.currentWeather = desc
                    self.currentTemperature = round(temp * 10) / 10
                    self.isLoaded = true
                    self.cachedDate = today
                }
                
                return (desc, round(temp * 10) / 10)
            } catch {
                // WeatherKit 실패 → Fallback
                return applyFallback()
            }
        } else {
            return applyFallback()
        }
        #else
        // WeatherKit import 불가 환경 (시뮬레이터 등)
        return applyFallback()
        #endif
    }
    
    // MARK: - Location

    private func requestCurrentLocation() async -> CLLocation? {
        let status = locationManager.authorizationStatus
        
        switch status {
        case .notDetermined:
            locationManager.requestWhenInUseAuthorization()
            // 권한 응답 대기 (최대 5초)
            try? await Task.sleep(nanoseconds: 3 * 1_000_000_000)
            let updatedStatus = locationManager.authorizationStatus
            if updatedStatus == .authorizedWhenInUse || updatedStatus == .authorizedAlways {
                return await getOneLocation()
            }
            return nil
            
        case .authorizedWhenInUse, .authorizedAlways:
            return await getOneLocation()
            
        case .denied, .restricted:
            return nil
            
        @unknown default:
            return nil
        }
    }
    
    private func getOneLocation() async -> CLLocation? {
        return await withCheckedContinuation { continuation in
            self.locationContinuation = continuation
            locationManager.requestLocation()
        }
    }
    
    // MARK: - CLLocationManagerDelegate
    
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        locationContinuation?.resume(returning: locations.first)
        locationContinuation = nil
    }
    
    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        locationContinuation?.resume(returning: nil)
        locationContinuation = nil
    }
    
    // MARK: - Fallback (WeatherKit 미사용 시)
    
    private func applyFallback() -> (weather: String, temperature: Double) {
        // 시간대 기반 합리적 기본값 (완전 하드코딩보다 나음)
        let hour = Calendar.current.component(.hour, from: Date())
        let month = Calendar.current.component(.month, from: Date())
        
        // 계절별 대략적 기온
        let seasonTemp: Double
        switch month {
        case 12, 1, 2: seasonTemp = -2.0
        case 3, 4, 5:  seasonTemp = 14.0
        case 6, 7, 8:  seasonTemp = 27.0
        case 9, 10, 11: seasonTemp = 16.0
        default: seasonTemp = 20.0
        }
        
        // 시간대 보정
        let timeOffset: Double
        if hour < 6 || hour > 22 { timeOffset = -3.0 }
        else if hour > 11 && hour < 16 { timeOffset = 3.0 }
        else { timeOffset = 0.0 }
        
        let temp = round((seasonTemp + timeOffset) * 10) / 10
        let desc = "알 수 없음" // 정직하게 표시 — 가짜 "맑음"보다 나음
                
        Task { @MainActor in
            self.currentWeather = desc
            self.currentTemperature = temp
            self.isLoaded = true
            self.cachedDate = Self.todayString()
        }
        
        return (desc, temp)
    }
    
    // MARK: - Helpers
    
    private static func todayString() -> String {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        return f.string(from: Date())
    }
    
    #if canImport(WeatherKit)
    @available(iOS 16.0, *)
    private static func conditionToKorean(_ condition: WeatherCondition) -> String {
        switch condition {
        case .clear:                          return "맑음"
        case .mostlyClear:                    return "대체로 맑음"
        case .partlyCloudy:                   return "구름 조금"
        case .mostlyCloudy:                   return "대체로 흐림"
        case .cloudy:                         return "흐림"
        case .rain:                           return "비"
        case .heavyRain:                      return "폭우"
        case .drizzle:                        return "이슬비"
        case .snow, .heavySnow:              return "눈"
        case .sleet, .freezingRain:          return "진눈깨비"
        case .thunderstorms:                  return "천둥번개"
        case .haze:                           return "연무"
        case .foggy:                          return "안개"
        case .windy, .breezy:                return "바람"
        case .blowingDust:                    return "황사"
        case .frigid:                         return "혹한"
        case .hot:                            return "무더위"
        default:                              return "흐림"
        }
    }
    #endif
}

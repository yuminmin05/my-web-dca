import logging
import yfinance as yf
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def run_genetic_algorithm(assets, generations=50, pop_size=50):
    """
    อัลกอริทึมพันธุกรรม (GA) เพื่อทำการ Prediction สัดส่วนน้ำหนักหุ้น
    โดยอิงจากข้อมูลเชิงประวัติศาสตร์ (Historical Data) เพื่อหา Expected Return
    """
    if not assets:
        return {'expected_return': 0, 'sharpe_ratio': 0, 'weights': {}}

    try:
        # 1. ดึงข้อมูลราคาหุ้นจริง (เติม .BK สำหรับหุ้นไทย)
        tickers = [f"{s}.BK" for s in assets]
        
        # ใช้ yfinance ดึงข้อมูลย้อนหลัง 3 ปี
        data = yf.download(tickers, period="3y", progress=False)['Close']
        
        # เช็คว่าดึงข้อมูลสำเร็จไหม
        if data.empty:
            raise ValueError("ไม่สามารถดึงข้อมูลจาก Yahoo Finance ได้เลย")

        # 2. ทำความสะอาดข้อมูล (Data Preprocessing)
        # กรณีเลือกหุ้นหลายตัว yfinance จะส่งกลับมาเป็น DataFrame
        if isinstance(data, pd.DataFrame):
            # บางที yfinance เรียงชื่อคอลัมน์ใหม่ เราต้องดึงชื่อหุ้นที่ดึงได้จริงมาใช้
            valid_assets = [str(col).replace('.BK', '') for col in data.columns]
            # เติมข้อมูลที่แหว่งด้วยวันก่อนหน้า (Forward Fill)
            data = data.ffill().dropna()
        else:
            # กรณีเลือกหุ้นตัวเดียว มันจะส่งมาเป็น Series
            valid_assets = assets
            data = data.dropna()

        # 3. คำนวณ Prediction (คาดการณ์ผลตอบแทนและความเสี่ยง)
        returns = data.pct_change().dropna()

        # คาดการณ์ผลตอบแทนรายปี (Expected Return) และความแปรปรวนเกี่ยวเนื่อง (Covariance)
        # รองรับทั้งกรณี DataFrame (หลายสินทรัพย์) และ Series (สินทรัพย์เดียว)
        if isinstance(returns, pd.DataFrame):
            mean_returns = returns.mean().values * 252
            cov_matrix = returns.cov().values * 252
        else:
            # Series -> แปลงเป็น array ขนาด 1 และ covariance เป็นเมทริกซ์ 1x1
            mean_returns = np.array([returns.mean() * 252])
            cov_matrix = np.array([[returns.var() * 252]])

        num_assets = len(valid_assets)
        risk_free_rate = 0.02 # สมมติฐานดอกเบี้ยไร้ความเสี่ยงที่ 2%

        # กรณีเลือกหุ้นตัวเดียว ไม่ต้องรัน GA
        if num_assets == 1:
            ret = float(mean_returns)
            vol = float(returns.std() * np.sqrt(252))
            sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0
            return {'expected_return': ret, 'sharpe_ratio': sharpe, 'weights': {valid_assets[0]: 1.0}}

        # ==========================================
        # 4. เริ่มกระบวนการ Genetic Algorithm (GA) Optimization
        # ==========================================
        # สร้างประชากรเริ่มต้น (สุ่มน้ำหนักแบบหลายๆ รูปแบบ)
        population = np.random.rand(pop_size, num_assets)
        population = population / population.sum(axis=1)[:, np.newaxis]
        
        # Fitness Function (เราต้องการให้ Sharpe Ratio สูงที่สุด) 
        def calculate_fitness(weights):
            p_ret = np.sum(mean_returns * weights)
            p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return (p_ret - risk_free_rate) / p_vol if p_vol > 0 else -99
            
        # เริ่มกระบวนการจำลองวิวัฒนาการ
        for _ in range(generations):
            fitness = np.array([calculate_fitness(ind) for ind in population])
            
            # Selection
            fitness_norm = fitness - np.min(fitness)
            if np.sum(fitness_norm) == 0:
                prob = np.ones(pop_size) / pop_size
            else:
                prob = fitness_norm / np.sum(fitness_norm)
                
            parents = population[np.random.choice(pop_size, size=pop_size, p=prob)]
            
            next_gen = []
            for i in range(0, pop_size, 2):
                p1, p2 = parents[i], parents[(i+1)%pop_size]
                
                # Crossover
                alpha = np.random.rand()
                c1 = alpha * p1 + (1 - alpha) * p2
                c2 = (1 - alpha) * p1 + alpha * p2
                
                # Mutation (กลายพันธุ์ 10% เพื่อหาความเป็นไปได้ใหม่ๆ)
                if np.random.rand() < 0.1: c1 += np.random.randn(num_assets) * 0.05
                if np.random.rand() < 0.1: c2 += np.random.randn(num_assets) * 0.05
                    
                # Normalize ให้ผลรวมน้ำหนักกลับมาเป็น 100% เสมอ
                c1 = np.clip(c1, 0.001, 1); c1 /= np.sum(c1)
                c2 = np.clip(c2, 0.001, 1); c2 /= np.sum(c2)
                
                next_gen.extend([c1, c2])
                
            population = np.array(next_gen)[:pop_size]
            
        # 5. หาผู้ชนะ (The Best Weights)
        final_fitness = np.array([calculate_fitness(ind) for ind in population])
        best_idx = np.argmax(final_fitness)
        best_weights = population[best_idx]
        
        # คำนวณ Prediction สุดท้ายที่จะส่งไปแสดงผล
        best_ret = np.sum(mean_returns * best_weights)
        best_vol = np.sqrt(np.dot(best_weights.T, np.dot(cov_matrix, best_weights)))
        best_sharpe = (best_ret - risk_free_rate) / best_vol
        
        # จัดรูปแบบ Dictionary ให้ง่ายต่อการอ่าน { 'PTT': 0.45, 'AOT': 0.55 }
        weight_dict = {valid_assets[i]: float(best_weights[i]) for i in range(num_assets)}
        
        return {
            'expected_return': float(best_ret),
            'sharpe_ratio': float(best_sharpe),
            'weights': weight_dict
        }
    except Exception as e:
        logger.exception("GA Optimizer failed")
        # คืนค่าเริ่มต้นที่เป็นกลาง แทนที่จะใช้ค่า optimistic ที่อาจทำให้ผู้ใช้เข้าใจผิด
        if assets:
            equal_w = {s: 1.0/len(assets) for s in assets}
        else:
            equal_w = {}
        return {
            'expected_return': 0.0,
            'sharpe_ratio': 0.0,
            'weights': equal_w
        }
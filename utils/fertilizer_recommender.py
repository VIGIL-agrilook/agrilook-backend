import math

def recommend_fertilizers(service, prescription, base_or_top, top_n=3):
	if base_or_top == "base":
		need_N = float(prescription.get('pre_Fert_N', 0))
		need_P = float(prescription.get('pre_Fert_P', 0))
		need_K = float(prescription.get('pre_Fert_K', 0))
	else:
		need_N = float(prescription.get('post_Fert_N', 0))
		need_P = float(prescription.get('post_Fert_P', 0))
		need_K = float(prescription.get('post_Fert_K', 0))

	result = []
	for fert in service.recommend_products(need_N, need_P, need_K, base_or_top, top_n):
		supplied_N = float(fert.get("grade", {}).get("N", 0))
		supplied_P = float(fert.get("grade", {}).get("P2O5", 0))
		supplied_K = float(fert.get("grade", {}).get("K2O", 0))
		bag_kg = float(fert.get("bag_kg", 20))
		usage_kg = (need_N / supplied_N * bag_kg) if supplied_N else 0
		supplied_P_total = usage_kg * supplied_P / 100 if supplied_P else 0
		supplied_K_total = usage_kg * supplied_K / 100 if supplied_K else 0
		shortage_P_kg = max(0, need_P - supplied_P_total)
		shortage_K_kg = max(0, need_K - supplied_K_total)
		bags = round(usage_kg / bag_kg, 2) if bag_kg else 0
		result.append({
			"K_ratio": supplied_K,
			"N_ratio": supplied_N,
			"P_ratio": supplied_P,
			"bags": bags,
			"fertilizer_id": fert.get("_id", ""),
			"fertilizer_name": fert.get("name", ""),
			"need_K_kg": need_K,
			"need_N_kg": need_N,
			"need_P_kg": need_P,
			"shortage_K_kg": round(shortage_K_kg, 2),
			"shortage_P_kg": round(shortage_P_kg, 2),
			"usage_kg": round(usage_kg, 2)
		})
	return result

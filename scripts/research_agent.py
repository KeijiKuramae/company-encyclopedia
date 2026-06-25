import os
import csv
import datetime
from google import genai
from google.genai import types

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return

    # Initialize client
    client = genai.Client(api_key=api_key)
    
    csv_file = "companies.csv"
    companies = []
    target_company = None
    
    # Read companies.csv
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            companies.append(row)
            if row['Status'] == 'Pending' and not target_company:
                target_company = row['Company Name']
    
    if not target_company:
        print("No pending companies found.")
        return

    print(f"Researching {target_company}...")
    
    # Read user profile
    profile_file = "my_profile.md"
    user_profile = ""
    if os.path.exists(profile_file):
        with open(profile_file, 'r', encoding='utf-8') as f:
            user_profile = f.read()

    profile_instruction = ""
    if user_profile:
        profile_instruction = f"""
    また、以下は私の現在の専攻・研究内容・興味関心です。
    【私のプロフィール】
    {user_profile}
    
    この情報を元に、企業とのマッチ度合いを評価してください。
    """
    
    # Construct prompt
    prompt = f"""
    あなたはプロのAI企業リサーチャーです。
    「{target_company}」について、最新のWeb情報を検索し、詳細なレポートを作成してください。
    
    【厳守するルール】
    - 「就職エージェントとして」や「分析のエキスパートとして」などの自己紹介や前置き、文末の挨拶は一切出力しないでください。
    - 客観的かつプロフェッショナルなトーンで統一してください。
    - 出力は必ず「# {target_company} 企業研究レポート」の見出しから開始し、Markdown形式のみを出力してください。
    
    {profile_instruction}
    
    【調査・出力項目】
    # {target_company} 企業研究レポート
    
    ## 🎯 私とのマッチ度評価 (総合評価: ★1〜5)
    (プロフィール情報に基づき、この企業の研究開発や事業内容と、私の専攻・興味との関連性を★の数で評価し、その理由や入社後に活かせる強みを簡潔に述べてください)

    ## 1. 企業概要
    事業内容や主要なプロダクト、企業のビジョンなど。
    
    ## 2. 理系院生向け情報 (R&D・技術力)
    - 研究開発(R&D)の注力分野
    - 保有しているコア技術・強み
    - 最近の技術的なニュースや特許・論文などの動向（もしあれば）
    
    ## 3. 待遇・福利厚生
    - 平均年収、初任給（特に院卒向け）
    - 福利厚生、家賃補助などの制度
    - ワークライフバランス、残業時間、働きやすさに関する評判
    
    ## 4. キャリアパス
    - 理系出身者の主な配属先・職種
    - 採用実績（大学院など）
    - 入社後のキャリアイメージ、研修制度
    
    ## 5. インターンシップ情報（院進予定者向け・持ち越し可否）
    - 学部4年/修士進学予定者が参加できるインターンシップの有無
    - 「インターンで得た評価や早期選考パスを、大学院卒業時（30卒）まで持ち越せるか（または通年採用か）」に関する情報・クチコミ
    - 特に「要件定義」「企画」「ITコンサルティング」「PdM」などの上流工程を体験できるプログラムの詳細

    
    必ずWeb検索を利用して、最新かつ正確な情報に基づいてレポートを作成してください。
    """

    # Generate content with fallback models
    models_to_try = ['gemini-3.5-flash', 'gemini-3.5-flash-8b', 'gemini-2.5-flash', 'gemini-1.5-pro']
    response = None
    last_error = None
    
    for m in models_to_try:
        try:
            print(f"Trying model: {m}...")
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3)
            )
            print(f"Successfully generated content using {m}!")
            break
        except Exception as e:
            print(f"Failed with {m}: {e}")
            last_error = e
            
    if not response:
        raise Exception(f"All models failed. Last error: {last_error}")
    
    report_content = response.text
    
    if not report_content or not report_content.strip():
        raise Exception("Generated report is empty! The model returned a blank response.")
    
    # Save the markdown file
    safe_company_name = target_company.replace(" ", "_").replace("/", "_")
    file_name = f"{safe_company_name}.md"
    file_path = os.path.join("docs", "companies", file_name)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"Saved report to {file_path}")
    
    # Update CSV status
    with open(csv_file, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Status'])
        writer.writeheader()
        for row in companies:
            if row['Company Name'] == target_company:
                row['Status'] = 'Done'
            writer.writerow(row)
            
    print(f"Updated {csv_file}")

if __name__ == "__main__":
    main()

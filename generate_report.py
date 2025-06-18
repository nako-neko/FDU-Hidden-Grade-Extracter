import json
from collections import OrderedDict

# --- 模块1: 数据处理 ---
def process_raw_grades(input_filename='grades.json'):
    """
    读取原始的 grades.json 文件，并在内存中对其进行分组和压缩。
    """
    print(f"步骤 1: 正在读取并处理原始文件 '{input_filename}'...")
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到原始文件 '{input_filename}'。")
        return None
    except json.JSONDecodeError:
        print(f"错误：无法解析 '{input_filename}' 中的JSON。")
        return None

    grades_by_semester = OrderedDict()
    for semester_block in full_data:
        grades_by_semester_id = semester_block.get('semesterId2studentGrades', {})
        for semester_id, grades_list in grades_by_semester_id.items():
            for course_grade in grades_list:
                semester_name = course_grade.get('semesterName')
                if not semester_name:
                    continue
                
                compressed_course = {
                    'courseName': course_grade.get('courseName'),
                    'gaGrade': course_grade.get('gaGrade'),
                    'gp': course_grade.get('gp'),
                    'gradeDetail': course_grade.get('gradeDetail')
                }
                
                if semester_name not in grades_by_semester:
                    grades_by_semester[semester_name] = []
                grades_by_semester[semester_name].append(compressed_course)
    
    print("数据处理完成。")
    return grades_by_semester

# --- 模块2: HTML报表生成 (UI美化版) ---
def generate_html_report(grades_data, output_filename='grades_report.html'):
    """根据处理好的成绩数据，生成一个美观的HTML报表。"""
    print(f"步骤 2: 正在生成 HTML 报告...")
    
    # 全新的CSS样式，采用炭黑/灰色系，设计更现代
    html_head = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>学生成绩报告</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');
            body { 
                font-family: 'Noto Sans SC', sans-serif;
                margin: 0;
                padding: 2rem;
                background-color: #f4f6f8; 
                color: #333;
            }
            .container {
                max-width: 900px;
                margin: auto;
                background: #ffffff;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }
            h1 { text-align: center; color: #2c3e50; margin-bottom: 0.5rem; }
            h2 { color: #34495e; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.5rem; margin-top: 2.5rem; }
            table { 
                width: 100%; 
                margin-top: 1.5rem;
                border-collapse: collapse; 
            }
            th, td { 
                padding: 1rem; 
                text-align: left; 
                border-bottom: 1px solid #ddd; 
            }
            thead th { 
                background-color: #34495e; /* 深灰蓝，替换掉原来的蓝色 */
                color: white; 
                font-weight: 700;
            }
            tbody tr:nth-child(even) { background-color: #f8f9fa; }
            tbody tr:hover { background-color: #e8ecf1; transition: background-color 0.3s; }
            footer { text-align: center; margin-top: 2rem; color: #7f8c8d; font-size: 0.9em; }
        </style>
    </head>
    """
    
    html_body_parts = ["<body>", "<div class='container'>", "<h1>学生成绩报告</h1>"]
    
    for semester_name, courses in grades_data.items():
        html_body_parts.append(f"<h2>{semester_name}</h2>")
        html_body_parts.append("<table><thead><tr><th>课程名称</th><th>等级</th><th>绩点</th><th>成绩详情</th></tr></thead><tbody>")
        for course in courses:
            # ... (这部分逻辑和之前一样)
            course_name = course.get('courseName', 'N/A')
            grade = course.get('gaGrade', 'N/A')
            gp = course.get('gp')
            gp_str = str(gp) if gp is not None else 'N/A'
            grade_detail_list = course.get('gradeDetail', [])
            grade_detail_str = ', '.join(filter(None, grade_detail_list))
            html_body_parts.append(f"<tr><td>{course_name}</td><td>{grade}</td><td>{gp_str}</td><td>{grade_detail_str}</td></tr>")
        html_body_parts.append("</tbody></table>")
        
    html_body_parts.append("<footer>报告生成时间: " + "2025-06-18" + "</footer>") # 动态添加页脚
    html_body_parts.append("</div></body></html>")
    
    final_html = html_head + "\n".join(html_body_parts)
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_html)
        print(f" -> HTML报告已保存到 '{output_filename}'。")
    except IOError as e:
        print(f"\n错误：写入HTML文件时发生错误: {e}")

# --- 模块3: Markdown报表生成 ---
def generate_markdown_report(grades_data, output_filename='grades_report.md'):
    """根据处理好的成绩数据，生成一个紧凑的Markdown表格报表。"""
    print(f"步骤 3: 正在生成 Markdown 报告...")
    report_lines = ["# 学生成绩报告\n"]
    for semester_name, courses in grades_data.items():
        report_lines.append(f"## {semester_name}\n")
        report_lines.append("| 课程名称 | 等级 | 绩点 | 成绩详情 |")
        report_lines.append("|:---|:---:|:---:|:---|")
        for course in courses:
            # ... (这部分逻辑和之前一样)
            course_name = course.get('courseName', 'N/A')
            grade = course.get('gaGrade', 'N/A')
            gp = course.get('gp')
            gp_str = str(gp) if gp is not None else 'N/A'
            grade_detail_list = course.get('gradeDetail', [])
            grade_detail_str = ', '.join(filter(None, grade_detail_list))
            report_lines.append(f"| {course_name} | {grade} | {gp_str} | {grade_detail_str} |")
        report_lines.append("\n")

    final_report = "\n".join(report_lines)
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(final_report)
        print(f" -> Markdown报告已保存到 '{output_filename}'。")
    except IOError as e:
        print(f"\n错误：写入Markdown文件时发生错误: {e}")

# --- 主函数入口 ---
def main():
    """主函数，负责调度整个流程。"""
    processed_data = process_raw_grades('grades.json')
    
    if processed_data:
        generate_html_report(processed_data)
        generate_markdown_report(processed_data)
        print("\n所有报告生成完毕！")

if __name__ == '__main__':
    main()

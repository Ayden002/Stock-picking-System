"""
实用工具脚本 - 包含辅助功能
"""
import os
import csv
import pandas as pd
from datetime import datetime
from logger import get_logger

logger = get_logger(__name__)

class ResultViewer:
    """结果查看器"""
    
    @staticmethod
    def view_latest_results():
        """查看最新的筛选结果"""
        results_file = 'data/stock_filter_results.csv'
        
        if not os.path.exists(results_file):
            print("✗ 未找到结果文件")
            return
        
        try:
            df = pd.read_csv(results_file, encoding='utf-8-sig')
            
            # 分离通过和不通过的
            passed = df[df['通过筛选'] == '是']
            
            print("\n" + "="*100)
            print("最新筛选结果")
            print("="*100)
            
            print(f"\n【通过筛选的股票】({len(passed)}个)")
            print("-" * 100)
            
            if len(passed) > 0:
                # 显示通过的股票
                for idx, row in passed.iterrows():
                    print(f"\n{idx+1}. {row['代码']}")
                    print(f"   日期: {row['日期']}")
                    print(f"   价格: ¥{row['最新收盘价']}")
                    print(f"   周线金叉: {row['周线金叉']}")
                    if pd.notna(row['涨停日期']) and row['涨停日期'] != '':
                        print(f"   涨停日期: {row['涨停日期']}")
                    print(f"   最大涨幅: {row['最大涨幅']}")
                    if pd.notna(row['倍量日期']) and row['倍量日期'] != '':
                        print(f"   倍量日期: {row['倍量日期']}")
                    print(f"   最大倍数: {row['最大倍数']}")
            else:
                print("暂无通过筛选的股票")
            
            print(f"\n【统计信息】")
            print("-" * 100)
            print(f"总检查数: {len(df)}")
            print(f"通过数: {len(passed)}")
            print(f"通过率: {len(passed)/len(df)*100:.2f}%")
            
            print("\n" + "="*100 + "\n")
            
        except Exception as e:
            print(f"✗ 读取结果文件失败: {str(e)}")

class DataExporter:
    """数据导出器"""
    
    @staticmethod
    def export_to_txt(format_type='simple'):
        """导出结果为文本格式
        
        Args:
            format_type: 'simple' 或 'detailed'
        """
        results_file = 'data/stock_filter_results.csv'
        
        if not os.path.exists(results_file):
            print("✗ 未找到结果文件")
            return
        
        try:
            df = pd.read_csv(results_file, encoding='utf-8-sig')
            passed = df[df['通过筛选'] == '是']
            
            if len(passed) == 0:
                print("✗ 没有通过筛选的股票")
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'data/stock_list_{timestamp}.txt'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("本地智能选股系统 - 筛选结果\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"筛选条件: 周线金叉 + 15日涨停 + 5日倍量\n")
                f.write("="*80 + "\n\n")
                
                for idx, row in passed.iterrows():
                    f.write(f"代码: {row['代码']}\n")
                    if format_type == 'detailed':
                        f.write(f"  日期: {row['日期']}\n")
                        f.write(f"  价格: {row['最新收盘价']}\n")
                        f.write(f"  周线金叉: {row['周线金叉']}\n")
                        if pd.notna(row['涨停日期']) and row['涨停日期'] != '':
                            f.write(f"  涨停日期: {row['涨停日期']}\n")
                        f.write(f"  最大涨幅: {row['最大涨幅']}\n")
                        if pd.notna(row['倍量日期']) and row['倍量日期'] != '':
                            f.write(f"  倍量日期: {row['倍量日期']}\n")
                        f.write(f"  最大倍数: {row['最大倍数']}\n")
                    f.write("\n")
                
                f.write("="*80 + "\n")
                f.write(f"总计: {len(passed)} 个通过筛选的股票\n")
            
            print(f"✓ 已导出到 {output_file}")
            
        except Exception as e:
            print(f"✗ 导出失败: {str(e)}")

class QuickAnalysis:
    """快速分析工具"""
    
    @staticmethod
    def show_statistics():
        """显示统计信息"""
        results_file = 'data/stock_filter_results.csv'
        
        if not os.path.exists(results_file):
            print("✗ 未找到结果文件")
            return
        
        try:
            df = pd.read_csv(results_file, encoding='utf-8-sig')
            passed = df[df['通过筛选'] == '是']
            
            print("\n" + "="*60)
            print("统计分析")
            print("="*60)
            
            print(f"\n【基本统计】")
            print(f"  总检查股票数: {len(df)}")
            print(f"  通过筛选: {len(passed)} ({len(passed)/len(df)*100:.1f}%)")
            print(f"  未通过: {len(df)-len(passed)} ({(len(df)-len(passed))/len(df)*100:.1f}%)")
            
            if len(passed) > 0:
                print(f"\n【通过筛选股票统计】")
                
                # 价格统计
                try:
                    passed['价格'] = passed['最新收盘价'].str.replace('¥', '').astype(float)
                    print(f"  平均价格: ¥{passed['价格'].mean():.2f}")
                    print(f"  最高价格: ¥{passed['价格'].max():.2f}")
                    print(f"  最低价格: ¥{passed['价格'].min():.2f}")
                except:
                    pass
                
                # 涨幅统计
                try:
                    passed['涨幅'] = passed['最大涨幅'].str.replace('%', '').astype(float)
                    print(f"\n  平均最大涨幅: {passed['涨幅'].mean():.2f}%")
                    print(f"  最大涨幅: {passed['涨幅'].max():.2f}%")
                    print(f"  最小涨幅: {passed['涨幅'].min():.2f}%")
                except:
                    pass
                
                # 倍数统计
                try:
                    passed['倍数'] = passed['最大倍数'].str.replace('x', '').astype(float)
                    print(f"\n  平均最大倍数: {passed['倍数'].mean():.2f}x")
                    print(f"  最大倍数: {passed['倍数'].max():.2f}x")
                    print(f"  最小倍数: {passed['倍数'].min():.2f}x")
                except:
                    pass
            
            print("\n" + "="*60 + "\n")
            
        except Exception as e:
            print(f"✗ 统计失败: {str(e)}")

def interactive_menu():
    """交互菜单"""
    while True:
        print("\n" + "="*60)
        print("本地选股系统 - 工具菜单")
        print("="*60)
        print("\n1. 查看最新筛选结果")
        print("2. 导出简单格式文本")
        print("3. 导出详细格式文本")
        print("4. 显示统计信息")
        print("5. 开始新的筛选")
        print("6. 对指定股票进行分析")
        print("0. 退出")
        
        choice = input("\n请选择 (0-6): ").strip()
        
        if choice == '1':
            ResultViewer.view_latest_results()
        elif choice == '2':
            DataExporter.export_to_txt('simple')
        elif choice == '3':
            DataExporter.export_to_txt('detailed')
        elif choice == '4':
            QuickAnalysis.show_statistics()
        elif choice == '5':
            os.system('python main.py')
        elif choice == '6':
            code = input("请输入股票代码: ").strip()
            if code:
                os.system(f'python analyze.py {code}')
        elif choice == '0':
            print("\n再见！")
            break
        else:
            print("✗ 无效选择")

if __name__ == '__main__':
    interactive_menu()

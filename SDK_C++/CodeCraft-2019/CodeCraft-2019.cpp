#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>

using namespace std;

void SplitString(const string& s, vector<string>& v, const string& c)
{
	string::size_type pos1, pos2;
	pos2 = s.find(c);
	pos1 = 0;
	while(string::npos != pos2)
	{
		v.push_back(s.substr(pos1, pos2-pos1));

		pos1 = pos2 + c.size();
		pos2 = s.find(c, pos1);
	}
	if(pos1 != s.length())
		v.push_back(s.substr(pos1));
}

vector<vector<int>> read_txt(string filePath)
{
	ifstream file(filePath);
	string file_str;
	getline(file,file_str);
	int num = count(file_str.begin(),file_str.end(),',');
	vector<int> file_info(num + 1);
	vector<vector<int>> file_info_all;
	while (getline(file,file_str))
	{
		vector<string> v;
		file_str.erase(file_str.begin());
		file_str.erase(file_str.end()-1);
		SplitString(file_str, v, ", ");
		for(int i = 0; i < file_info.size(); i++)
		{
			file_info[i] = stoi(v[i]);
		}
		file_info_all.push_back(file_info);
	}
	return file_info_all;
}
void write_txt(string filePath ,vector<vector<int>> answer_path)
{
	ofstream answer(filePath);
	if(answer.is_open())
	{
		for (int i = 0; i < answer_path.size(); ++i) {
			answer << "(";
			for (int j = 0; j < answer_path[i].size(); ++j) {
				answer << to_string(answer_path[i][j]) ;
				if (j != answer_path[i].size() - 1)
				{
					answer << ", ";
				}
			}

			answer << ")" << endl;
		}
		answer.close();
	}
}

void creat_map_array(vector<vector<int>> cross, vector<vector<int>> road, vector<vector<int>>& dis_array,vector<vector<int>>& road_array)
{
	int a = cross.size();
	int n = road.size();
	int road_id;
	int road_length;
	int start_node;
	int end_node;
	int isDuplex;
	vector<int> dis_vector(a);
	vector<int> road_vector;
	for (int i = 0; i < a; ++i) {
		for (int j = 0; j < a; ++j) {
			if(i != j)
			{
				dis_vector[j] = 10000;
			}
			else
			{
				dis_vector[j] = 0;
			}
		}
		dis_array.push_back(dis_vector);
	}
	for (int i = 0; i < a; ++i) {
		for (int j = 0; j < a; ++j) {
			road_vector.push_back(0);
		}
		road_array.push_back(road_vector);
	}
	for (int i = 0; i < n; ++i) {
		for (int j = 0; j < road[i].size(); ++j) {
			road_id = road[i][0];
			road_length = road[i][1];
			start_node = road[i][4] - 1;
			end_node = road[i][5] - 1;
			isDuplex = road[i][6];
			if (isDuplex == 1)
			{
				dis_array[start_node][end_node] = road_length;
				dis_array[end_node][start_node] = road_length;
				road_array[start_node][end_node] = road_id;
				road_array[end_node][start_node] = road_id;
			} else
			{
				dis_array[start_node][end_node] = road_length;
				road_array[start_node][end_node] = road_id;
			}
		}
	}
}

vector<int> DijkstraMinPath(int start, int end, vector<vector<int>> L) {
	int n = L.size();
	int dis[n];        //存储源点到各个顶点的最短路径
	vector<int> path[n];
//    vector<vector<int>> all_path;
	for (int i = 0; i < n; i++) //initial
	{
		dis[i] = L[start][i];
		path[i].push_back(start);//初始化起点位置?
		path[i].push_back(i);
	}
	for (int i = 1 ;i < n ; i++)
	{
		for (int j = 0 ; j < n ; j++)
		{
			if (dis[i] > dis[j] + L[j][i])
			{
				dis[i] = dis[j] + L[j][i];
				path[i].clear();
				path[i].insert(path[i].end(), path[j].begin(), path[j].end());
				path[i].push_back(i);
			}
		}
		for (int m = 0; m < i; m++)
		{
			for (int j = 0; j < n; j++)
			{
				if (dis[m] > dis[j] + L[j][m])
				{
					dis[m] = dis[j] + L[j][m];
					path[m].clear();                     //保存并更新路径
					path[m].insert(path[m].end(), path[j].begin(), path[j].end());
					path[m].push_back(m);
				}
			}
		}
	}
	return path[end];
}

vector<vector<int>> all_car_path(vector<vector<int>> map_array, vector<vector<int>> map_road_array, vector<vector<int>> car_inf)
{
	int car_len = car_inf.size();
	//如何给path初始化
	vector<int> path;
	vector<vector<int>> path_road;

	for (int i = 0; i < car_len; i++)
	{
		path = DijkstraMinPath(car_inf[i][1] - 1, car_inf[i][2] - 1, map_array);
		int path_len = path.size()-1;
		//path_center的类型
		vector<int> path_center;
		for (int j = 0; j < path_len;j++)
		{
			path_center.push_back(map_road_array[path[j]][path[j+1]]);
		}
		int time = i / 11;
		vector<int> answer_line;
		answer_line.push_back(car_inf[i][0]);
		answer_line.push_back(max(car_inf[i][4], time));
		for (int j = 0; j < path_center.size(); ++j) {
			answer_line.push_back(path_center[j]);
		}
		path_road.push_back(answer_line);
	}

	return path_road;
}

int main(int argc, char *argv[])
{
    cout << "Begin" << endl;
	
	if(argc < 5){
		cout << "please input args: carPath, roadPath, crossPath, answerPath" << endl;
		exit(1);
	}
	
	string carPath(argv[1]);
	string roadPath(argv[2]);
	string crossPath(argv[3]);
	string answerPath(argv[4]);
	
	cout << "carPath is " << carPath << endl;
	cout << "roadPath is " << roadPath << endl;
	cout << "crossPath is " << crossPath << endl;
	cout << "answerPath is " << answerPath << endl;
	
	// TODO:read input filebuf
    vector<vector<int>> cross_info_all = read_txt(crossPath);
    vector<vector<int>> car_info_all = read_txt(carPath);
    vector<vector<int>> road_info_all = read_txt(roadPath);
	// TODO:process
    vector<vector<int>> dis_array;
    vector<vector<int>> road_array;
    creat_map_array(cross_info_all, road_info_all, dis_array, road_array);
    vector<vector<int>> answer = all_car_path(dis_array, road_array,car_info_all);
	// TODO:write output file
    write_txt(answerPath, answer);
	return 0;
}

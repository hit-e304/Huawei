#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <iterator>
#include <fstream>
#include <stack>
#include <ctime>
#include <unordered_map>
#include <exception>

using namespace std;

int car_per_sec = 50;
int interval_time = 1;
int car_in_map = 3500;


void BubbleSort(vector<int> &a)
{
    bool flag = true;
    int k = (int)a.size();
    while (flag)
    {
        flag = false;
        for (int i = 1; i < k; i++)
        {
            if (a[i - 1] < a[i]) {
                swap(a[i - 1], a[i]);
                flag = true;
            }
        }
        k--;
    }
}


// 快速排序
// 找中枢（挖坑填数）
int Partition(vector<int> &a, int left, int right)
{
    int flag = a[left];
    while (left < right)
    {
        while (a[right] >= flag&&left < right)
            right--;
        if (left < right)
        {
            a[left] = a[right];
            left++;
        }

        while (a[left] < flag&&left < right)
            left++;
        if (left < right)
        {
            a[right] = a[left];
            right--;
        }
    }
    a[left] = flag;
    return left;
}

void QuicksortSection(vector<int> &a, int left, int right)
{
    if (left < right)
    {
        int i = Partition(a, left, right);
        QuicksortSection(a, left, i -1);
        QuicksortSection(a, i + 1, right);
    }
}

void Quicksort(vector<int> &a)
{
    int n = (int)a.size();
    int left = 0;
    int right = n - 1;
    QuicksortSection(a, left, right);
}



vector<vector<double>> initZeroTraceMatrix(int raw, int colum){
    vector<vector<double>> matrix;
    vector<double> temp_array(colum, 10000.00);

    for(int i = 0; i < raw; i++){
        temp_array[i] = 0.00;
        matrix.push_back(temp_array);
        temp_array[i] = 10000.00;
    }

    return matrix;
}

vector<vector<int>> initSameNumberMatrix(int raw, int colum, int initNumber){
    vector<int> tempRaw(colum, initNumber);
    vector<vector<int>> matrix(raw, tempRaw);

    return matrix;
}

// Equivalent to "append" in Python
void arrayExtend(vector<double> &a, vector<double> &b){
    int sizeb = (int)b.size();
    for(int i = 0; i < sizeb; i++){
        a.push_back(b[i]);
    }
}

void addMatrixToMatrix(vector<vector<int>> &m1, vector<vector<int>> &m2){
//    for(auto i : m2){
//        m1.push_back(i);
//    }
    int len = (int)m2.size();
    for(int i = 0; i < len; i++)
        m1.push_back(m2[i]);
}

int pop(vector<int> &array){
    int topNumber = array.back();
    array.pop_back();

    return topNumber;
}

double sum(vector<double> &array){
    double summary = 0.0;
    for(auto i : array){
        summary += i;
    }
    return summary;
}

int max(int a, int b){
    if(a > b)
        return a;
    return b;
}

int min(int a , int b){
    if(a < b)
        return a;
    return b;
}

double minf(double a , double b){
    if(a < b)
        return a;
    return b;
}

double maxf(double a , double b){
    if(a < b)
        return a;
    return b;
}

double mind(double a , double b){
    if(a < b)
        return a;
    return b;
}

double maxd(double a , double b){
    if(a < b)
        return a;
    return b;
}

double ABS(double x){
    if(x < 0.0)
        return -x;
    return x;
}

int minOrMaxNumberIndex(vector<double> array, bool mode){
    int i = 0;
    int index = 0;
    double number = array[0];
    int len = (int)array.size();
    if(mode){
        for(i = 0; i < len; i++){
            if(number > array[i]){
                index = i;
                number = array[i];
            }
        }

    }
    else {
        for (i = 0; i < len; i++) {
            if (number < array[i]) {
                index = i;
                number = array[i];
            }
        }
    }
    return index;
}


// Equivalent to " is in " in Python
bool elementIsInArray(int a, vector<int> B){
    int sizeB = (int)B.size();
    for(int i = 0; i < sizeB; i++){
        if(a == B[i])
            return true;
    }
    return false;
}


vector<int> djikstraPathSearch(int start, int end, vector<vector<double >> L) {
    int n = (int)L.size();
    double dis[n];        //鐎涙ê鍋嶅┃鎰仯閸掓澘鎮囨稉顏堛€婇悙鍦畱閺堚偓閻叀鐭惧?
    vector<int> path[n];
    for (int i = 0; i < n; i++) //initial
    {
        dis[i] = L[start][i];
        path[i].push_back(start);//閸掓繂顫愰崠鏍崳閻愰€涚秴缂?
        path[i].push_back(i);
    }
    for (int i = 1; i < n; i++) {
        for (int j = 0; j < n; j++) {
            if (dis[i] > dis[j] + L[j][i]) {
                dis[i] = dis[j] + L[j][i];
                path[i].clear();
                path[i].insert(path[i].end(), path[j].begin(), path[j].end());
                path[i].push_back(i);
            }
        }
        for (int m = 0; m < i; m++) {
            for (int j = 0; j < n; j++) {
                if (dis[m] > dis[j] + L[j][m]) {
                    dis[m] = dis[j] + L[j][m];
                    path[m].clear();                     //娣囨繂鐡ㄩ獮鑸垫纯閺傛媽鐭惧?
                    path[m].insert(path[m].end(), path[j].begin(), path[j].end());
                    path[m].push_back(m);
                }
            }
        }
    }
    return path[end];
}


// Equivalent to "str,split(",")" in Python
vector<string> splitString(const string& s, const string& c)
{
    vector<string> v;
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
    return v;
}

void eraseStringSpace(string &str){
    int index = 0;
    if( !str.empty()){
        while( (index = (int)str.find(' ',index)) != string::npos){
            str.erase(index,1);
        }
    }
}

vector<int> convertStringsToIntegers(vector<string> str){
    int lenStr = (int)str.size();
    vector<int> integers;
    for(int i = 0; i < lenStr; i++){
        integers.push_back(stoi(str[i]));
    }
    return integers;
}

vector<vector<int>> readFileInf(string path){
    ifstream readFile(path);
    string tempStr;
    vector<string> splitedString;
    vector<int> singleLineNumbers;
    vector<vector<int>> allFileNumbersMatrix;
    while(getline(readFile,tempStr)){
        if(tempStr[0] != '#'){
            eraseStringSpace(tempStr);
            splitedString = splitString(splitString(splitString(tempStr, "(")[1], ")")[0], ",");
            singleLineNumbers = convertStringsToIntegers(splitedString);
            allFileNumbersMatrix.push_back(singleLineNumbers);
        }
    }
    readFile.close();
    return  allFileNumbersMatrix;
}

void map_graph(vector<vector<int>> &cross, vector<vector<int>> &road, vector<vector<double>> &array_dis, vector<vector<int>> &array_road, vector<vector<double>> &array_loss){
    int lenCross = (int)cross.size();
    // int lenRoad = (int)road.size();
    array_dis = initZeroTraceMatrix(lenCross, lenCross);
    array_road = initSameNumberMatrix(lenCross, lenCross, 0);

    int name, length, channel, speed_lim, start_id, end_id, is_dux;
    for(auto i : road){
        name = i[0];
        length = i[1];
        channel = i[2];
        speed_lim = i[3];
        start_id = i[4] - 1;
        end_id = i[5] - 1;
        is_dux = i[6];
        if(is_dux){
            array_dis[start_id][end_id] = array_dis[end_id][start_id] = (double)length;
            array_road[start_id][end_id] = array_road[end_id][start_id] = name;
        }
        else{
            array_dis[start_id][end_id] = length;
            array_road[start_id][end_id] = name;
        }
    }
    array_loss = array_dis;
}

/*
 * record_road() untested.
 */
void record_road(vector<vector<int>> &batch, vector<double> &road_use_list, vector<double> &road_percent_list, int road_id_bias){
    for(auto i : batch){
        for(auto j = i.begin() + 2; j != i.end(); j++){
            road_use_list[j[0]-road_id_bias] += 1;
        }
    }
    double sum_use = sum(road_use_list);
    int a = (int)road_use_list.size();
    for(int i = 0; i < a; i++){
        road_percent_list[i] = road_use_list[i] / sum_use;
    }
}

unordered_map<int, vector<int>> speed_split(vector<vector<int>> &car_inf){
    int max_speed = 0;

    for(auto i : car_inf){
        if(i[3] > max_speed){
            max_speed = i[3];
        }
    }
    vector<vector<int>> car_divide_speed(max_speed);
    for(auto i : car_inf){
        car_divide_speed[i[3] - 1].push_back(i[0]);
    }
    unordered_map<int, vector<int>> output_dic = {};
    for(int i = 0; i < max_speed; i++){
        output_dic[i+1] = car_divide_speed[i];
    }
    return output_dic;
}

vector<vector<int>> time_split(vector<int> group, int car_per_sec, int interval_time, int speed){
    vector<vector<int>> group_divide_time;
    vector<int> cur_batch;
    int group_len = (int)group.size();
    int car_per_batch;
    int batch_num;

    if(speed <= 2){
        car_per_batch = car_per_sec * interval_time;
    }
    else if(speed <= 4){
        car_per_batch = int(car_per_sec * interval_time * 1.1);
    }
    else if(speed <= 6){
        car_per_batch = int(car_per_sec * interval_time * 1.1);
    }
    else{
        car_per_batch = int(car_per_sec * interval_time * 1.1);
    }

    batch_num = int(group_len / car_per_batch) + 1;
    int len = 0;
    for(int i = 0; i < batch_num; i++){
        cur_batch.clear();
        if(group.size() < car_per_batch){
            len = (int)group.size();
        }
        else{
            len = car_per_batch;
        }
        for(int j = 0; j < len; j++){
            cur_batch.push_back(pop(group));
        }

        group_divide_time.push_back(cur_batch);
    }

    return group_divide_time;
}

vector<int> update_car(vector<int> &final_time, int time){
    vector<int> new_final_time;
    for(auto i : final_time){
        if(i > time){
            new_final_time.push_back(i);
        }
    }
    return new_final_time;
}

void cal_car_path(vector<vector<double>> &map_loss_array, vector<vector<int>> &map_road_array, vector<vector<int>> &car_inf, vector<int> &batch, int car_id_bias, int road_bias, vector<vector<int>> &road_inf, int speed, int time, vector<int> &final_time, vector<vector<int>> &path_road_time){
    vector<int> path;
    vector<int> path_center;
    int car_id = 0;
    double run_time = 0.0;
    path_road_time.clear();
    for(auto i : batch){
        car_id = i - car_id_bias;
        path = djikstraPathSearch(car_inf[car_id][1]-1, car_inf[car_id][2]-1, map_loss_array);
        path_center.clear();
        int a = (int)path.size();
        path_center.push_back(car_inf[car_id][0]);
        path_center.push_back(max(car_inf[car_id][4], time));
//        cout << path_center[1]<< endl;
        for (int j = 0; j < a - 1; ++j) {
            path_center.push_back((int)map_road_array[path[j]][path[j+1]]);
        }
        path_road_time.push_back(path_center);

        run_time = 0.0;
        for(auto k = path_center.begin() + 2; k != path_center.end(); k++){
            run_time += road_inf[k[0]-road_bias][1] * 1.0 / min(speed, road_inf[k[0]-road_bias][2]);
        }
        final_time.push_back(int(run_time) + 1 + time);
    }
}


void update_loss(vector<vector<double>> &array_loss, vector<vector<double>> &array_dis, vector<vector<int>> &road_inf, vector<double> &road_percent_list, int road_id_bias, int speed, unordered_map<int, double> &cross_loss){
    int name, length, channel, speed_lim, start_id, end_id, is_dux;
    double use_rate;
    double loss;
    for(auto i : road_inf){
        name = i[0] - road_id_bias;
        length = i[1];
        channel = i[2];
        speed_lim = i[3];
        start_id = i[4] - 1;
        end_id = i[5] - 1;
        is_dux = i[6];
        use_rate = road_percent_list[name];
        loss = 1.00 * length * (1.0 / min(speed_lim, speed) + 60.23 * 1.00 * use_rate / channel) + 0.65 * maxd(cross_loss[start_id+1], cross_loss[end_id+1]);

        if(is_dux){
            array_loss[start_id][end_id] = array_loss[end_id][start_id] = loss;
        }
        else{
            array_loss[start_id][end_id] = loss;
        }
    }
}

unordered_map<int, double> cal_cross_loss(vector<vector<int>> &cross_inf, vector<vector<int>> &road_inf){
    unordered_map<int, double> road_flow = {};
    unordered_map<int, double> cross_loss = {};
    double loss;
    for(auto road : road_inf){
        road_flow[road[0]] = 1.00 * road[3] * road[3] / road[2];
    }
    for(auto cross : cross_inf){
        loss = 0.00;
        for(int i = 1; i < 5; i++){
            if(cross[i] == -1){
                continue;
            }
            for(int j = 1; j < 5; j++){
                if(cross[j] == -1){
                    continue;
                }
                loss += ABS(road_flow[cross[i]] - road_flow[cross[j]]);
            }
        }
        cross_loss[cross[0]] = loss;
    }
    return cross_loss;
}



int main(int argc, char *argv[]) {
    if(argc < 5){
        std::cout << "please input args: carPath, roadPath, crossPath, answerPath" << std::endl;
        exit(1);
    }

    std::string carPath(argv[1]);
    std::string roadPath(argv[2]);
    std::string crossPath(argv[3]);
    std::string answerPath(argv[4]);


    vector<vector<int>> cross_inf = readFileInf(crossPath);
    vector<vector<int>> car_inf = readFileInf(carPath);
    vector<vector<int>> road_inf = readFileInf(roadPath);

    ///////////////////////////////////////////////////////
    clock_t startTime = clock();
    vector<vector<double>> map_dis_array;
    vector<vector<int>> map_road_array;
    vector<vector<double>> map_loss_array;
    unordered_map<int, double> cross_loss;
    unordered_map<int, vector<int>> car_divide_speed;


    map_graph(cross_inf, road_inf, map_dis_array, map_road_array, map_loss_array);
    cross_loss = cal_cross_loss(cross_inf, road_inf);
    car_divide_speed = speed_split(car_inf);

/////////////////////////////////////////////////////////////////////////
    int time = 1;
    // int all_time = 0;
    int car_id_bias = car_inf[0][0];
    int road_id_bias = road_inf[0][0];
    vector<vector<int>> answer;
    vector<int> speed_list;
    vector<int> final_time;
    vector<double> road_use_list(road_inf.size(), 0.0);
    vector<double> road_percent_list(road_inf.size(), 0.0);
    vector<int> cur_group;
    vector<vector<int>> group_divide_time;
    int batch_len = 0;
    vector<vector<int>> batch_path_time;

    for(auto& speed : car_divide_speed){
        speed_list.push_back(speed.first);
    }
    BubbleSort(speed_list);
//    for(auto i : car_divide_speed[8])
//        cout << i << ",";
/////////////////////////////////////////////////////////////////////////////
    for(auto speed : speed_list){
        cur_group = car_divide_speed[speed];
        if(cur_group.empty()){

            continue;
        }
        group_divide_time = time_split(cur_group, car_per_sec, interval_time, speed);
        for(auto batch : group_divide_time){
            batch_len = (int)batch.size();
            while(final_time.size() > (car_in_map - batch_len)){
                time++;
                final_time = update_car(final_time, time);
            }
            cal_car_path(map_loss_array, map_road_array, car_inf, batch, car_id_bias, road_id_bias, road_inf, speed, time, final_time, batch_path_time);
            time += interval_time;
            addMatrixToMatrix(answer, batch_path_time);
            record_road(batch_path_time, road_use_list, road_percent_list, road_id_bias);
            update_loss(map_loss_array, map_dis_array, road_inf, road_percent_list, road_id_bias, speed, cross_loss);
//            cout << time << endl;
        }

    }
    clock_t endTime = clock();
    cout << endTime - startTime << endl;


    ofstream fout(answerPath);
    int len = (int)answer.size();
    for(int i = 0; i < len; i++){
        int len1 = (int)answer[i].size();
        fout << "(";
        for(int j = 0; j < len1; j++){
            if(j != len1 - 1){
                fout << answer[i][j] << ", ";
            }
            else{
                fout << answer[i][j] << "";
            }
        }
        fout << ")" << endl;
    }
///////////////////////////////////////////////////////////////




    return 0;
}

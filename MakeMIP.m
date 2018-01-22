%% Create proper framework for MIP on the dataset

% Allocate Field Matrix
n_Fields = 55;
FieldString = cell(n_Fields,1);
for f = 1:n_Fields;
    FieldString{f} = sprintf('%3.3d',f);
end
FieldStorage = repmat(FieldString,n_Fields,1);


% Allocate WellName

RowLetter = [{'B'};{'C'}];
RowNumberTop = [{'02'};{'03'};{'04'};{'05'}];
RowNumberBottom = [{'05'};{'04'};{'03'};{'02'}];

WellStorage = [];

for CurrentRow = 1:length(RowLetter);
    for CurrentColumn = 1:length(RowNumberTop);
        String = cell(1,1);
        if mod(CurrentRow,2) == 0;
            CurrentString = [RowLetter{CurrentRow},RowNumberBottom{CurrentColumn}];
        else
            CurrentString = [RowLetter{CurrentRow},RowNumberTop{CurrentColumn}];
        end
        
        String{1,1} = CurrentString;
               
        ReppedString = repmat(String,16,1);
        WellStorage = [WellStorage;ReppedString];   
    end
end
           
% Load Actual Images, make MIP and save as PNG
parfor CurrentSTK = 1:440;
    CurrentImage = tiffread2(['STK/','20170116_BeadsDistribution_1_ledRFP_s',num2str(CurrentSTK),'.stk']);
    StackLength = size(CurrentImage,2);
    
    ImageWidth = CurrentImage.width;
    ImageHeigth = CurrentImage.height;
    
    ImageMatrix = zeros(ImageHeigth,ImageWidth,StackLength);
    ImageMatrix = uint16(ImageMatrix);
    
    for CurrentStack = 1:StackLength
        ImageMatrix(:,:,CurrentStack) = CurrentImage(CurrentStack).data;
    end
    
    MaxProject = max(ImageMatrix,[],3);
    StorageString = ['TIFF/','20170116_BeadsDistribution_',WellStorage{CurrentSTK},'_T0001F0',FieldStorage{CurrentSTK},'L01A01Z01C01.png'];
    imwrite(MaxProject,StorageString)  
end
 